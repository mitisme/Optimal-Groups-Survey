import csv    

def clean_up(input_df):
    # drop the second row and last row of the DataFrame
    cleaned_df = input_df.drop([0, input_df.index[-1]])
    cleaned_df.reset_index(drop=True, inplace=True)
    print(cleaned_df)
    return cleaned_df
