def calculate_pathway_matches(pathways_df, user_preferences, importance_weights):
    """
    Calculate how well each pathway matches the user's preferences.
    
    Args:
        pathways_df (DataFrame): The pathways dataframe
        user_preferences (dict): The user's preferred ranges for each metric
        importance_weights (dict): The importance weights for each metric
        
    Returns:
        list: A list of tuples (pathway_id, match_score, match_explanation)
            sorted by match score in descending order
    """
    pathway_matches = []
    
    # Calculate the match for each pathway
    for _, pathway in pathways_df.iterrows():
        # Initialize variables
        total_importance = 0
        total_score = 0
        match_explanation = {}
        
        # Check each metric that the user has expressed preferences for
        for metric, (min_pref, max_pref) in user_preferences.items():
            # Skip if this pathway doesn't have this metric
            if metric not in pathway['metrics']:
                continue
                
            # Get the pathway's value for this metric
            pathway_value = pathway['metrics'][metric]['value']
            
            # Calculate how well the pathway matches the user's preference for this metric
            if min_pref <= pathway_value <= max_pref:
                # Perfect match
                metric_score = 100
                match_explanation[metric] = f"Matches your preference ({min_pref}-{max_pref})"
            elif pathway_value < min_pref:
                # Below the minimum preference
                distance = min_pref - pathway_value
                if distance <= 2:
                    # Close match
                    metric_score = 80 - (distance * 15)
                    match_explanation[metric] = f"Slightly below your preference ({pathway_value} vs {min_pref}-{max_pref})"
                else:
                    # Poor match
                    metric_score = 50 - (distance * 10)
                    match_explanation[metric] = f"Below your preference ({pathway_value} vs {min_pref}-{max_pref})"
            else:
                # Above the maximum preference
                distance = pathway_value - max_pref
                if distance <= 2:
                    # Close match
                    metric_score = 80 - (distance * 15)
                    match_explanation[metric] = f"Slightly above your preference ({pathway_value} vs {min_pref}-{max_pref})"
                else:
                    # Poor match
                    metric_score = 50 - (distance * 10)
                    match_explanation[metric] = f"Above your preference ({pathway_value} vs {min_pref}-{max_pref})"
                    
            # Apply the importance weight
            metric_score *= importance_weights[metric]
            total_score += metric_score
            total_importance += importance_weights[metric]
            
        # Calculate the overall match score (0-100)
        if total_importance > 0:
            match_score = total_score / total_importance
        else:
            match_score = 0
            
        # Add this pathway to the list
        pathway_matches.append((pathway['id'], match_score, match_explanation))
        
    # Sort the pathways by match score in descending order
    pathway_matches.sort(key=lambda x: x[1], reverse=True)
    
    return pathway_matches
