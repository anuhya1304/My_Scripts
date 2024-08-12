#AutoCAD Turbine Model Block Generator
import pandas as pd
import pyautocad

def load_excel_data(file_path):
    """Load Excel data into a DataFrame."""
    return pd.read_excel(file_path)

def filter_by_model(df, model_name):
    """Filter the DataFrame by turbine model."""
    return df[df['Turbine Model'] == model_name]

def create_block(acad, block_name, blade_radius, foundation_radius, points):
    """Create a block in AutoCAD with circles and a polyline."""
    center = pyautocad.APoint(0, 0)
    block = acad.doc.Blocks.Add(center, block_name)
    block.AddCircle(center, float(blade_radius))
    block.AddCircle(center, float(foundation_radius))
    polygon = pyautocad.aDouble(points)
    block.AddPolyline(polygon)
    return block

def insert_block(acad, block_name, df):
    """Insert the block at specified coordinates in AutoCAD."""
    for _, row in df.iterrows():
        insertion_point = pyautocad.APoint(row['Latitudes'], row['Longitudes'])
        acad.model.InsertBlock(insertion_point, block_name, 1, 1, 1, 0)

def main(excel_path, coordinates_path, model_name, block_name):
    acad = pyautocad.Autocad()
    
    # Load data
    df2 = load_excel_data(excel_path)
    df1 = load_excel_data(coordinates_path)
    
    # Filter by turbine model
    df_model = filter_by_model(df2, model_name)
    
    # Extract points for polyline
    points = []
    blade_swept_path_radius = int(df_model['Blade swept path Radius'].iloc[0])
    foundation_radius = int(df_model['Foundation Radius'].iloc[0])
    for _, row in df_model.iterrows():
        points.extend([row['X'], row['y'], row['z']])
    
    # Create block
    create_block(acad, block_name, blade_swept_path_radius, foundation_radius, points)
    
    # Insert block at specified coordinates
    insert_block(acad, block_name, df1)
    
    print("Blocks inserted successfully in AutoCAD.")

# Parameters for reuse
excel_path = r'path_to_excel_with_turbine_data.xlsx'
coordinates_path = r'path_to_excel_with_coordinates.xlsx'
model_name = 'V162 - 5.6 MW'
block_name = 'MyBlock1'

# Execute the main function
main(excel_path, coordinates_path, model_name, block_name)
