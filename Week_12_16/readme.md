# Talent Recommendation Engine

## Introduction

In today’s highly competitive job market, connecting the right candidate with the appropriate job position is more critical than ever. Historically, manual evaluation of each applicant was the main screening procedure, but it was time-consuming and prone to human biases and errors. To address this challenge, we have developed a Talent Recommendation Engine.

## Previous Solutions

Historically, candidate-job matching has been tackled through methods such as keyword matching and early machine learning approaches. However, these methods lacked the depth of analysis needed for a precise matching process.

## Problem Definition & Objectives

Our main goal is to create an intelligent and automated process that can match candidates to job opportunities based on three factors: language skills, working experience, and skills. We aim to extract these three aspects from resumes and create a ranking algorithm to arrange resumes in order of preference.

## Experimental Setup

### Dataset

Our dataset includes 13 unique job descriptions and 126 resumes. After preprocessing, we successfully processed 124 resumes.

### Text Extraction

We explored various PDF parsing solutions and found PDFMiner to be the most accurate for text extraction.

### Initial Approach Using TF-IDF

Initially, we used TF-IDF for ranking, but it resulted in low accuracy.

### Parsing

We explored conventional NLP methods, pre-existing resume parsers, and Large Language Models (LLMs) for parsing.

### Prompt Engineering

Prompt engineering was crucial for accurate data parsing, especially for complex CVs.

### Embeddings

We used ADA-002 text embeddings for computing similarity scores.

## Final Proposed Approach

Our approach involves data preprocessing, parsing, and ranking:

### Data Preprocessing

- Text Extraction
- Text Cleaning

### Parsing

- Parsing Job Descriptions
- Parsing Resumes
- Combining Parsed Elements

### Ranking

Our ranking process considers language proficiencies, years of experience, skills, and job titles.

## Streamlit

We built an intuitive user interface using the Streamlit framework for easy interaction with the ranking engine.

## Results and Discussion

Our approach significantly improved accuracy compared to traditional TF-IDF ranking. However, there's room for improvement, especially in handling job titles and domain-specific skills.

## Conclusion and Future Improvements

Our Talent Recommendation Engine demonstrates promise in automating candidate-job matching. Future improvements should focus on enhancing data quality, embeddings, and developing a dedicated Large Language Model (LLM) for resume parsing.

---

**Note:** This README provides an overview of the Talent Recommendation Engine project. For detailed implementation and code, please refer to the project files.

