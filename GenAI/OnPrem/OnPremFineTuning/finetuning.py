import torch
import json
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from peft import LoraConfig, get_peft_model, PeftModel
from trl import SFTTrainer
import warnings
warnings.filterwarnings("ignore")

# --- CONFIGURATION ---
model_id = "facebook/opt-125m" # A very small model from hugging face for fast demonstration
output_dir = "./lora_sentiment_finetuned"
MERGED_MODEL_PATH = "./final_merged_model_for_inference" # New path for the final merged model
DATA_FILE = "training_data.jsonl" # Your new JSON Lines file
OUTPUT_RESULTS_FILE = "output.json"
TEST_PROMPT = "Instruction: Give me a review of QuantumFlow 7.\nResponse:"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- 1. Load Model and Tokenizer with Quantization (QLoRA Setup) ---
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4", # NormalFloat4-bit quantization
    bnb_4bit_compute_dtype=torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token # Fixes 'pad_token not set' errors by using the existing EOS token to fill empty space in data batches.

# Load the base model (will be used for the 'BEFORE' test)
base_model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config if DEVICE == "cuda" else None, # Only apply QLoRA if on GPU
    torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
    device_map="auto"
)

"""
# We dont want model to use previous weights because we want to update the weights, that is why we are disabling cache
Disables the Key/Value (KV) Cache for the model.

The KV Cache is an optimization to speed up sequential generation (inference)
by storing previously computed attention key and value vectors.

When using memory-saving techniques like gradient checkpointing during training,
this cache must be disabled (set to False) because gradient checkpointing relies
on recomputing those exact intermediate states during the backward pass 
for memory saving, the pre-stored cache (which lacks the necessary gradient tracking) 
must be disabled

"""
base_model.config.use_cache = False # Required for gradient checkpointing which is required to calculate weight updates during training. If this is not set to False, the model will throw an error about "Cannot use cached key/values when gradient checkpointing is enabled."

# --- DEMO A: TEST BEFORE FINE-TUNING ---
print("\n" + "="*50)
print("DEMO A: MODEL BEFORE FINE-TUNING (Base Model Test)")
print("="*50)

inputs_before = tokenizer(TEST_PROMPT, return_tensors="pt").to(DEVICE)
with torch.no_grad():
    outputs_before = base_model.generate(**inputs_before, max_new_tokens=30, temperature=0.7)
response_before = tokenizer.decode(outputs_before[0], skip_special_tokens=True).split('Response:')[-1].strip()

print(f"PROMPT: {TEST_PROMPT.strip()}")
print(f"RESPONSE (Base Model): {response_before}")
print("Note: Response should be generic or non-committal.")

# --- 2. Load Dataset from JSON Lines File ---
try:
    # Use the Hugging Face datasets library to load the local JSONL file
    dataset = load_dataset('json', data_files=DATA_FILE, split="train")
    print(f"\nSuccessfully loaded {len(dataset)} examples from {DATA_FILE}")
except Exception as e:
    print(f"\nERROR: Could not load dataset file '{DATA_FILE}'. Ensure it exists and is valid JSON Lines format.")
    print(f"Details: {e}")
    exit()

def formatting_func(example):
    # This formats the data into the instruction-response structure
    return f"Instruction: {example['instruction']}\nResponse: {example['output']}"

# --- 3. Configure PEFT (LoRA) ---
"""
r (int): 
        The **rank** of the update matrices. This is the dimension of the 
        low-rank matrices injected into the model's layers. A higher value (e.g., 32 or 64) 
        increases the expressive capacity of the adapter but also increases the number of 
        trainable parameters and VRAM consumption. The value 16 is a balanced starting point.

    lora_alpha (int): 
        The **scaling factor** applied to the LoRA updates.
        A higher alpha gives the LoRA updates a stronger influence over the pre-trained weights.

    target_modules (list[str]): 
        A list of string names corresponding to the module layers in the base model 
        where the LoRA adapters should be injected. 
        - `["q_proj", "v_proj"]` targets the **Query** and **Value** projection matrices 
          in the Transformer's attention mechanism, which is a highly effective and memory-efficient 
          choice for most generative models.

    lora_dropout (float): 
        The dropout probability to be applied to the LoRA *adapter* layers during training. 
        It helps to regularize the small set of trainable parameters and prevent overfitting 
        to the fine-tuning data. The value 0.05 is a typical small dropout rate.

    bias (str): 
        Specifies which bias terms (if any) should be trained.
        - `"none"`: Only the LoRA weights ($A$ and $B$ matrices) are trained. Bias terms are frozen.
          This is generally the recommended and most common setting.
        - `"all"`: All bias parameters in the target modules are trained.
        - `"lora_only"`: Only the bias parameters added by the LoRA layers are trained.

    task_type (str):
        Defines the type of task the model is being fine-tuned for. This is primarily used 
        by the PEFT library to correctly configure the model wrapper and identify modules.
        - `"CAUSAL_LM"`: Causal Language Modeling, used for next-token prediction/text generation 
          (e.g., GPT, Llama, Mistral models).
"""
lora_config = LoraConfig(
    r=16, 
    lora_alpha=32, 
    target_modules=["q_proj", "v_proj"], 
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# Apply LoRA to the model
model_to_train = get_peft_model(base_model, lora_config)
print("\n" + "="*50)
print("DEMO B: PEFT EFFICIENCY (Trainable Parameters)")
print("="*50)
# DEMONSTRATION POINT: Show trainable params
trainable_params_info = model_to_train.print_trainable_parameters() 

# --- 4. Setup and Run Trainer ---
training_args = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=5,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4, 
    learning_rate=2e-4,
    logging_steps=1,
    fp16=(DEVICE == "cuda"), 
    save_strategy="epoch",
    report_to="none" # Disable external logging for simplicity
)

# Supervised Fine-Tuning (SFT): Training a pre-trained language model (LLM) 
trainer = SFTTrainer(
    model=model_to_train,
    args=training_args,
    train_dataset=dataset,
    formatting_func=formatting_func,
    processing_class=tokenizer,
)

print("\n--- Starting LoRA Fine-Tuning (Training should be very fast) ---")
trainer.train()

# --- 5. Merge and Save the Final Model ---

# Save the LoRA Adapters first (good practice)
trainer.model.save_pretrained(output_dir)
print(f"\nLoRA adapters saved to {output_dir}")

# Reload base model and load LoRA weights (merging them)
# A fresh load to ensure the base model is pristine and not in QLoRA state
model_for_merge = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
    device_map="auto"
)
# Load the LoRA adapter onto the base model
model_for_merge = PeftModel.from_pretrained(model_for_merge, output_dir)

# Perform the merge and get the final, full model
merged_model = model_for_merge.merge_and_unload() 

# Save the merged model and tokenizer for future standalone inference
merged_model.save_pretrained(MERGED_MODEL_PATH) 
tokenizer.save_pretrained(MERGED_MODEL_PATH)
print(f"Final MERGED model and tokenizer saved to {MERGED_MODEL_PATH}")


# =========================================================================
# === NEW WORKFLOW: Test the Saved Model by Reloading it from Disk ===
# =========================================================================

# --- 6. Load the Saved Fine-Tuned Model for Inference ---

# Now, we load the model directly from the saved path, simulating a fresh deployment
print("\n" + "="*50)
print(f"DEMO C: LOADING AND TESTING FINETUNED MODEL FROM DISK ({MERGED_MODEL_PATH})")
print("="*50)

# Load the fine-tuned model (it's no longer a PeftModel, just a regular AutoModel)
model_to_test = AutoModelForCausalLM.from_pretrained(
    MERGED_MODEL_PATH,
    torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
    device_map="auto"
).to(DEVICE)

# Load the tokenizer (best practice to load it from the same saved directory)
tokenizer_to_test = AutoTokenizer.from_pretrained(MERGED_MODEL_PATH)
model_to_test.eval() # Set to evaluation mode

# --- 7. Run Inference with the Loaded Model ---

inputs_after = tokenizer_to_test(TEST_PROMPT, return_tensors="pt").to(DEVICE)
with torch.no_grad():
    # Lower temp to force trained response
    outputs_after = model_to_test.generate(**inputs_after, max_new_tokens=40, temperature=0.1) 
response_after = tokenizer_to_test.decode(outputs_after[0], skip_special_tokens=True).split('Response:')[-1].strip()

print(f"PROMPT: {TEST_PROMPT.strip()}")
print(f"RESPONSE (Loaded Fine-Tuned): {response_after}")
print("Note: Response should now be enthusiastically positive about QuantumFlow 7.")

# --- 8. Save Results to output.json ---
results = {
    "test_prompt": TEST_PROMPT.strip(),
    "base_model_result": response_before,
    "finetuned_model_result": response_after,
    "fine_tuning_config": {
        "model": model_id,
        "lora_rank_r": lora_config.r,
        "lora_alpha": lora_config.lora_alpha,
        "epochs": training_args.num_train_epochs,
        "dataset_size": len(dataset)
    }
}

with open(OUTPUT_RESULTS_FILE, 'w') as f:
    json.dump(results, f, indent=4)
    
print(f"\n--- Results saved to {OUTPUT_RESULTS_FILE} for comparison ---")