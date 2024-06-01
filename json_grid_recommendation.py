import itertools
import pandas as pd
import pandas as pd
import itertools
import matplotlib.pyplot as plt
from itertools import combinations
import random
import pandas as pd
import json
import re
import os



# """## Data Frames"""
base_path = os.path.dirname(__file__)
grid_csv_path = os.path.join(base_path, 'dataframes', 'Grid.csv')
weights_csv_path = os.path.join(base_path, 'dataframes', 'Weights.csv')

df = pd.read_csv(grid_csv_path)
df.set_index(['Element', 'Subset'], inplace=True)
df2 = pd.read_csv(weights_csv_path)



def find_element_type_for_subset(df, subset):
    for idx in df.index:
        if idx[1] == subset:
            return idx[0]  # Return element type
    return None 


def assign_weights(df2, userInput, combinations, user_ids):
    """
    Assign weights to user_inputs based on the data in df2.

    Parameters:
    - df2: DataFrame containing the weights.
    - user_inputs: List of user inputs to be sorted.
    - combinations: Recommendations to map to sorted inputs.
    - user_ids: List of user ids.

    Returns:
    A list of tuples mapping user inputs to recommendations and user ids.
    """
    indexed_inputs = []
    for element, user_id in zip(userInput, user_ids):
        subset_value = element[1]
        indexed_inputs.append((element[0], subset_value, user_id))

    sorted_inputs = sorted(indexed_inputs, key=lambda x: df2.set_index('Subset')['Combined Weight'].get(x[1], 0), reverse=True)
    sorted_recommendations = sorted(combinations, key=lambda x: int(x[0].rstrip('%').rstrip('V').rstrip('H')) if x[0].isdigit() else 0, reverse=True)

    timeline_ids = [item[1] for item in sorted_inputs]

    recommendations = [(timeline_ids[i], sorted_recommendations[i], user_id) for i, (_, _, user_id) in enumerate(sorted_inputs)]

    return recommendations


def recommend_grids(df, df2, json_data):
    """
    Recommend grids based on user input.

    Parameters:
    - df: DataFrame containing available grid combinations.
    - df2: DataFrame containing weights.
    - user_inputs: List of tuples containing user input.
    - user_ids: List of user ids.

    Returns:
    A list of dictionaries containing recommended grids.
    """

    data = json.loads(json_data)


    # Extract user_subsets and user_ids from the dictionary
    user_subsets = data["user_subsets"]
    user_ids = data["user_ids"]


    userInput = [(find_element_type_for_subset(df, subset), subset) for subset in user_subsets]
    userInput = [input for input in userInput if input[0] is not None]

    user_subsets = [t[1] for t in userInput]

    user_rows = df.loc[userInput]
    available_percentages = [row.index[row].tolist() for _, row in user_rows.iterrows()]
    all_combinations = list(itertools.product(*available_percentages))

    valid_combinations = [combo for combo in all_combinations
                          if sum(int(percent.split('%')[0]) for percent in combo) in (100, 99)
                          and combo != ('33% H', '33% H', '33% H')]

    if len(user_subsets) == 1:
    # Use the user ID from the first element in user_ids, as there's only one subset.
     return [[(userInput[0][1], '100%', user_ids[0])]]

    def is_symmetric(combination):
        has_H = any('H' in combo for combo in combination)
        has_V = any('V' in combo for combo in combination)
        return not (has_H and has_V)

    valid_combinations = list(filter(is_symmetric, valid_combinations))

    if valid_combinations:
        return [assign_weights(df2, userInput, combo, user_ids) for combo in valid_combinations]
    else:
        subset_weights = df2[df2['Subset'].isin(user_subsets)]['Combined Weight']
        highest_weight_element = subset_weights.idxmax()
        top_subset = df2['Subset'][highest_weight_element]
        # print(f"""For {top_subset}, the recommended grid is 100% """)
        other = [t for t in userInput if t[1] != top_subset]
        # return recommend_grids(df, df2, other, user_ids)
        result = recommend_grids(df, df2, json.dumps({"user_subsets": [t[1] for t in other], "user_ids": user_ids}))
        # recommendation = [(top_subset, '100%')]
        recommendation = [(top_subset, '100%', user_ids[user_subsets.index(top_subset)])]

        result.append(recommendation)
        return result


def split_combinations(lst):
    if not lst:
        return [[]]
    combinations = []
    for i in range(1, len(lst)):
        for combo in split_combinations(lst[i:]):
            combinations.append([lst[:i]] + combo)
    return combinations


def filter_unique_recommendations(recommendations):
    seen_recommendations = set()
    unique_results = []

    for recommendation in recommendations:
        recommendation_tuple = tuple(recommendation.items())

        if recommendation_tuple not in seen_recommendations:
            seen_recommendations.add(recommendation_tuple)
            unique_results.append(recommendation)

    return unique_results


def convert_to_json(input_data):
    output = {"recommendations": []}

    for sublist in input_data:
        recommendation = []

        for item in sublist:
            # Assuming that 'item' is a tuple like (subset_name, percentage, user_id)
            subset_name = item[0]  # This corresponds to 'Element_Subset' in your data
            element_id = str(item[2])
            
            # Extract the base element type and specific subset from the subset name
            # Splitting by '_' and taking the first part as the element type
            # and the second part (if available) as the subset
            parts = subset_name.split('_')
            element_type_base = parts[0].lower() if len(parts) > 0 else ''
            subset = parts[1] if len(parts) > 1 else ''

            # Mapping base element type to full element type name
            element_type_mapping = {
                'paragraph': "Paragraph",
                'bullettitle': "Bullet Title",
                'bulletbody': "Bullet Body",
                'imageportrait': "Image Portrait",
                'imagesquare': "Image Square",
                'imagelandscape': "Image Landscape",
                'table': "Table",
                'quote': "Quote",
                'list': "List",
                'cycle': "Cycle",
                'process': "Process",
                'timeline': "Timeline",
                'funnel': "Funnel",
                'pyramid': "Pyramid"
            }
            
            element_type = element_type_mapping.get(element_type_base, "Unknown")

            # Assuming 'item[1]' is a string that contains the size percentage and direction
            size_direction = item[1].split()
            size = size_direction[0]  # The size percentage (e.g., '100%')
            direction = size_direction[1] if len(size_direction) > 1 else 'None'

            recommendation.append({
                "id": element_id,
                "elementType": element_type,
                "subset": subset,
                "size": size,
                "direction": direction
            })

        output["recommendations"].append(recommendation)

    return output

def filter_recommendations(recommendations):
    filtered_recommendations = []
    seen_combinations = set()

    for recommendation in recommendations:
        # Sort the recommendation to ensure consistent order
        sorted_recommendation = sorted(recommendation, key=lambda x: (x["elementType"], x["subset"], x["size"], x["direction"]))
        combination = tuple((elem["elementType"], elem["subset"], elem["size"], elem["direction"]) for elem in sorted_recommendation)

        # Check if the combination has been seen before
        if combination not in seen_combinations:
            # Check if all elements with the same elementType and subset have the same size and direction
            elem_type_subset_map = {}
            for elem in sorted_recommendation:
                key = (elem["elementType"], elem["subset"])
                if key not in elem_type_subset_map:
                    elem_type_subset_map[key] = (elem["size"], elem["direction"])
                else:
                    if elem_type_subset_map[key] != (elem["size"], elem["direction"]):
                        break
            else:
                filtered_recommendations.append(recommendation)
                seen_combinations.add(combination)
    return filtered_recommendations
