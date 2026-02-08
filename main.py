import pandas as pd
from datetime import datetime, timedelta
import random

# Create the data (100 records)
num_records = 100

# Generate sample data
data = {
    'Request ID': [f'REQ{1000 + i}' for i in range(1, num_records + 1)],
    'Status': random.choices(['Active', 'Closed', 'On Hold', 'Cancelled','partially filled','zero filled'], 
                            weights=[40, 35, 15, 10, 5, 5], k=num_records),
    'Job Title': random.choices([
        'Software Engineer', 'Data Analyst', 'Project Manager', 'UX Designer',
        'DevOps Engineer', 'Product Manager', 'Marketing Specialist',
        'Sales Representative', 'HR Coordinator', 'Financial Analyst',
        'Business Analyst', 'Network Administrator', 'QA Tester',
        'Technical Writer', 'System Administrator'
    ], k=num_records),
    'Start Date': [(datetime.now() + timedelta(days=random.randint(-30, 90))).strftime('%Y-%m-%d') 
                   for _ in range(num_records)],
    'End Date': [(datetime.now() + timedelta(days=random.randint(30, 180))).strftime('%Y-%m-%d') 
                 for _ in range(num_records)],
    'Work Site Address': [f'{random.randint(100, 999)} {random.choice(["Main St", "Oak Ave", "Pine Rd", "Elm St", "Maple Dr", "Cedar Ln"])}, {random.choice(["New York", "San Francisco", "Chicago", "Austin", "Boston", "Seattle", "Denver", "Atlanta"])}, USA' 
                         for _ in range(num_records)],
    'Work Site Name': random.choices([
        'TechCorp Solutions', 'Innovate Inc', 'Global Systems Ltd',
        'Future Tech', 'Digital Innovations', 'Cloud Solutions Corp',
        'Data Systems Inc', 'Creative Minds LLC'
    ], k=num_records),
    'Total Positions': [random.randint(1, 10) for _ in range(num_records)],
    'Description': ['Sample job description' for _ in range(num_records)],
    'Max Submissions per Vending Status': [random.randint(1, 5) for _ in range(num_records)],
    'Full Name': random.choices([
        'John Smith', 'Emma Johnson', 'Michael Brown', 'Sarah Davis',
        'Robert Wilson', 'Jennifer Lee', 'David Miller', 'Lisa Taylor',
        'James Anderson', 'Maria Garcia'
    ], k=num_records),
    'Interviewed?': random.choices(['Yes', 'No', 'Scheduled'], weights=[30, 50, 20], k=num_records),
    'Hiring Manager': random.choices([
        'Alice Green', 'Bob White', 'Charlie Black', 'Diana Gray'], k=num_records)
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
df.to_csv('hiringman_with_diff_status.csv', index=False)
print("File saved as 'job_openings_dummy.csv'")