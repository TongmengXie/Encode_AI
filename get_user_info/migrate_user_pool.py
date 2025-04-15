#!/usr/bin/env python
"""
Migration script to move user_pool.csv from root directory to get_user_info directory
and set up the cache directory inside get_user_info.
"""
import os
import shutil
import pandas as pd

# Get the script directory path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

def migrate_user_pool():
    """Migrate user_pool.csv from root to get_user_info directory"""
    # Source and destination paths
    source_path = os.path.join(PARENT_DIR, "user_pool.csv")
    dest_path = os.path.join(SCRIPT_DIR, "user_pool.csv")
    
    # Create cache directory inside get_user_info
    cache_dir = os.path.join(SCRIPT_DIR, "cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Check if source file exists
    if os.path.exists(source_path):
        print(f"Found user_pool.csv in root directory: {source_path}")
        
        # Check if destination file exists
        if os.path.exists(dest_path):
            print(f"Destination file already exists: {dest_path}")
            print("Merging data from both files...")
            
            try:
                # Read both files
                source_df = pd.read_csv(source_path)
                dest_df = pd.read_csv(dest_path)
                
                # Merge data, removing duplicates
                merged_df = pd.concat([dest_df, source_df]).drop_duplicates().reset_index(drop=True)
                
                # Save merged data
                merged_df.to_csv(dest_path, index=False)
                print(f"Successfully merged data and saved to: {dest_path}")
                
                # Backup original file
                backup_path = os.path.join(PARENT_DIR, "user_pool.csv.bak")
                shutil.copy2(source_path, backup_path)
                print(f"Created backup of original file: {backup_path}")
                
            except Exception as e:
                print(f"Error merging files: {str(e)}")
                print("Copying source file as a fallback...")
                shutil.copy2(source_path, dest_path)
                print(f"Copied user_pool.csv to: {dest_path}")
        else:
            # Simply copy the file if destination doesn't exist
            try:
                shutil.copy2(source_path, dest_path)
                print(f"Copied user_pool.csv to: {dest_path}")
            except Exception as e:
                print(f"Error copying file: {str(e)}")
    else:
        print(f"No user_pool.csv found in root directory: {source_path}")
        
        # Create an empty user_pool.csv with the correct columns if it doesn't exist
        if not os.path.exists(dest_path):
            print("Creating empty user_pool.csv with header row...")
            default_columns = [
                'real_name', 'age_group', 'gender', 'nationality', 
                'preferred_residence', 'cultural_symbol', 'bucket_list',
                'healthcare_expectations', 'travel_budget', 
                'currency_preferences', 'insurance_type', 'past_insurance_issues'
            ]
            
            # Create empty DataFrame with correct columns
            empty_df = pd.DataFrame(columns=default_columns)
            empty_df.to_csv(dest_path, index=False)
            print(f"Created empty user_pool.csv at: {dest_path}")
    
    print("\nMigration complete!")
    print(f"user_pool.csv location: {dest_path}")
    print(f"Cache directory: {cache_dir}")

if __name__ == "__main__":
    migrate_user_pool() 