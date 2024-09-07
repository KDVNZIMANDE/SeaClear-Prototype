# TESTING adding pdf data to the DB
# DO NOT RUN!
# DO NOT RUN!
# DO NOT RUN!

import pymongo
import pdfplumber

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["coastal_water_quality"]
collection = db["water_quality_results"]

def extract_data_from_pdf(pdf_path):
    data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and len(row) > 1:
                        beach_name = row[0].strip() if row[0] else "Unknown Beach"
                        counts = [value.strip() for value in row[1:] if value and value.strip().isdigit()]
                        if beach_name and counts:
                            data.append({
                                "beach": beach_name,
                                "enterococci_counts": counts
                            })
    return data

# Insert data into MongoDB
def insert_data_into_mongodb(data):
    if data:
        collection.insert_many(data)

# Main function
def main():
    pdf_path = "CCT_coastal_water_quality_results_analysis_report.pdf"
    data = extract_data_from_pdf(pdf_path)
    
    # Print data for debugging
    print(data)
    
    insert_data_into_mongodb(data)
    print(f"Inserted {len(data)} records into MongoDB.")

if __name__ == "__main__":
    user_input = ""
    while (user_input != 'y' or user_input != 'n'):
        input("print are you sure you want to run (this does not work) (y/n)")
    if user_input =="y":
        main()

