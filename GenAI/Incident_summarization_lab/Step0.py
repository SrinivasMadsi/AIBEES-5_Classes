#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
import os
import io

def run_preprocessing():
    st.header("Data Overview and EDA")

    uploaded_file = st.file_uploader("Upload your incident data CSV file", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, encoding="latin1")
        st.success("File uploaded successfully!")
        st.subheader("Preview of the dataset:")
        st.dataframe(df.head())

        st.subheader("Exploratory Data Analysis")

        # Show incidents by category
        if 'Category' in df.columns:
            st.write("Incidents by Category:")
            category_counts = df['Category'].value_counts()
            st.bar_chart(category_counts)

        # Show incidents by subcategory
        if 'Subcategory' in df.columns:
            st.write("Incidents by Subcategory:")
            subcat_counts = df['Subcategory'].value_counts()
            st.bar_chart(subcat_counts)

        # Incidents over time
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            time_counts = df.groupby(df['Date'].dt.date).size()
            st.line_chart(time_counts)

        # Allow user to pick two columns for visualization
        columns = df.columns.tolist()
        col1 = st.selectbox("Select first column for bar chart", columns)
        col2 = st.selectbox("Select second column for bar chart", columns)

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader(f"Distribution of {col1}")
            st.bar_chart(df[col1].value_counts())

        with col_right:
            st.subheader(f"Distribution of {col2}")
            st.bar_chart(df[col2].value_counts())

        # Show missing values
        st.subheader("Data Cleaning")
        st.write("Missing Values in Each Column:")
        st.write(df.isnull().sum())

        if st.checkbox("Drop rows with missing values"):
            df = df.dropna()
            st.success("Rows with missing values dropped.")

        df.to_csv("inc_data_final.csv", index=False)
        st.success("Cleaned data saved as 'inc_data_final.csv'.")

