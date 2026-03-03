""" 
This module provides helper functionality for validating Wikipedia links. 
It filters out non-article namespaces (e.g., Category, File, Template), fragment links, empty links,
identifier pages, and already-visited pages.
"""
def is_valid_link(link: str,seen: set) -> bool:
    """
    Determine whether a Wikipedia href is worth following.
    Args:
        link (str): Raw href string
        seen (set): Set of visited page titles

    Returns:
        bool: True if the link should be followed, False otherwise
    """
    #
    EXCLUDED_PREFIXES = [
        "./Category:",
        "./Template:",
        "./Wikipedia:",
        "./Help:",
        "./File:",
        "./Image:",
        "./Talk:",
        "./User:",
        "./User_talk:",
        "./Portal:",
        "./Draft:",
        "./Module:",
        "./MediaWiki:",
        "./Special:",
        "./Book:",
        "./TimedText:",
        "./Gadget:",
        "./Template_talk:",
    ]
    
    EXCLUDED_SUFFIXES = [
        "_(identifier)",
    ]
    
    if any(link.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    
    if any(link.endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
        return False
    
    if "#" in link:
        return False
    
    if not link or link.strip() == "":
        return False
    
    #Normalise to the format used in 'seen'
    if link.replace('_', ' ').replace('./', '') in seen:
        return False
    
    return True