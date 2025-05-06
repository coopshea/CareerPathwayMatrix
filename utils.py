import streamlit as st

# Default images for the app
DEFAULT_IMAGES = {
    "career_path_1": "https://pixabay.com/get/g9847a867d11aa24b228ffb99ae5f7646156f114f599c65be6415242e01634f0de4a1319a62c4f29a43e399f14e36c4cb85d4fb523499474385624247c2e776f4_1280.jpg",
    "career_path_2": "https://pixabay.com/get/g8ac263d964b8cead02f797cbbdf3023eec9fdfe9a2fe04e6ac77c002163631b4860d37b91c9f334e0a887247a8f57a27aaa08313a41036b89c6953d82983c067_1280.jpg",
    "career_path_3": "https://pixabay.com/get/g6e3a13605f29b47b8101740897dfc81a71f9a4d580010b1fd59842e022cb2c00501b86b7249841b17565f773ea8ab51dd059be0819fa6857784dd6769a46f3e7_1280.jpg",
    "career_path_4": "https://pixabay.com/get/g6e73098677ac8593162a311eafa9e531966d23c188315e2240591470de583fb8df85e1c2cd6d80577172c4fc7be99494a393d0e0c1012d336a0b47f3fbfbf74a_1280.jpg",
    "data_viz_concept": "https://pixabay.com/get/gf640bfc3f071ca83f07e546c921eebe7a8516cd1677cbd4a4b9dd703c9e32859c6f4c55ffae988ebdcec22150e8b9639ff49fe7b136acf3cc3bbbe17b4dfe48b_1280.jpg",
    "data_viz_2": "https://pixabay.com/get/ge039fcb42b305155262990c8f470b58df2c2e3cfb3cd86cbea10ebaf25736025953ee347efdfb4636bf108ac79f3babbc855446fd5f86a447e435a97d886e600_1280.jpg",
    "data_viz_3": "https://pixabay.com/get/g8901478f123180595100a9d39a0076aa96e57beb75767e59296eb950e11e63faa2fa61c68e2a69fe391b6c3d7162ffef0e3849012f555ef6feca8c5fa88def51_1280.jpg",
    "career_decision_1": "https://pixabay.com/get/g3736f7c604275726b8d12365621b96563f561009360c3c47b3733d247de22832b5704650cca0e10743947c71987fd821f7a1b0928739b4ec3e722b545cff8ca0_1280.jpg",
    "career_decision_2": "https://pixabay.com/get/g4c340497092cfa4b26899aaf98c7933c9376cd5d65529a03eddce2b61e754a03d4c88606563c3cb9e28beffa249f98d1b4633466b1fd66ee0920f2ea6f314a35_1280.jpg",
    "career_decision_3": "https://pixabay.com/get/gbb1ba0d046f68cc1319b872be40544463b2bb4a7b44a6b4a34ab2a05fe4ab14713c54ff8de5a9afa935c2027a2dadf353b031be6def9e055526d2a3a51813255_1280.jpg"
}

def create_pathway_card(pathway, metrics_data):
    """
    Create a card for displaying a pathway in a simplified format.
    
    Args:
        pathway (dict): The pathway data
        metrics_data (dict): Information about the metrics
        
    Returns:
        str: HTML for the pathway card
    """
    # Extract key metrics
    risk = pathway['metrics'].get('risk_level', {}).get('value', 'N/A')
    probability = pathway['metrics'].get('success_probability', {}).get('value', 'N/A')
    terminal_value = pathway['metrics'].get('terminal_value', {}).get('value', 'N/A')
    time_to_return = pathway['metrics'].get('time_to_return', {}).get('value', 'N/A')
    
    # Create the HTML card
    html = f"""
    <div style="border:1px solid #ddd; border-radius:5px; padding:10px; margin:10px 0;">
        <h3>{pathway['name']}</h3>
        <p style="color:gray;">{pathway['category']}</p>
        <p>{pathway['description']}</p>
        <div style="display:flex; justify-content:space-between; margin-top:10px;">
            <span><b>Risk:</b> {risk}/10</span>
            <span><b>Success Probability:</b> {probability}/10</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:5px;">
            <span><b>Ceiling:</b> {terminal_value}/10</span>
            <span><b>Time to Return:</b> {time_to_return}/10</span>
        </div>
    </div>
    """
    
    return html
