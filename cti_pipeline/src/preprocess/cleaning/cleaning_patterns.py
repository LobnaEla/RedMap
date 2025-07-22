"""
Cleaning Patterns for CTI Text Preprocessing

This module contains all regex patterns used for cleaning CTI documents.
Patterns are organized by category for better maintainability.
"""

# HTML/Web content patterns to remove
HTML_PATTERNS = [
    r'<[^>]+>',  # HTML tags
    r'&[a-zA-Z0-9#]+;',  # HTML entities
    r'javascript:[^"\']*',  # JavaScript URLs
    r'onclick="[^"]*"',  # JavaScript events
    r'style="[^"]*"',  # Inline styles
    r'class="[^"]*"',  # CSS classes
]

# Boilerplate patterns commonly found in CTI documents
BOILERPLATE_PATTERNS = [
    r'This document is TLP:[A-Z]+.*?(?=\n\n|\.$)',
    r'Classification:\s*[A-Z\s]+.*?(?=\n\n|\.$)',
    r'Distribution:\s*[A-Z\s]+.*?(?=\n\n|\.$)',
    r'Page\s+\d+\s+of\s+\d+',
    r'All\s+rights\s+reserved.*?(?=\n\n|\.$)',
    r'©\s*\d{4}.*?(?=\n\n|\.$)',
    r'Copyright\s*\d{4}.*?(?=\n\n|\.$)',
    # Removed table of contents pattern as it might be too broad
]

# Advertisement patterns
AD_PATTERNS = [
    r'Advertisement.*?(?=\n\n|\.$)',
    r'Sponsored\s+by.*?(?=\n\n|\.$)',
    r'Click\s+here.*?(?=\n\n|\.$)',
    r'Subscribe\s+to.*?(?=\n\n|\.$)',
    r'Follow\s+us.*?(?=\n\n|\.$)',
    r'Like\s+us.*?(?=\n\n|\.$)',
    r'Share\s+this.*?(?=\n\n|\.$)',
]

# Navigation and UI element patterns (generic)
NAV_PATTERNS = [
    r'^\s*Homepage?\s*$',
    r'^\s*Open\s+in\s+app\s*$',
    r'^\s*Sign\s+in\s*$',
    r'^\s*Get\s+started\s*$',
    r'^\s*Home\s*$',
    r'^\s*About\s*$',
    r'^\s*Contact\s*$',
    r'^\s*Menu\s*$',
    r'^\s*Search\s*$',
    r'^\s*Login\s*$',
    r'^\s*Register\s*$',
    r'^\s*Subscribe\s*$',
    r'^\s*Follow\s*$',
    r'^\s*Following\s*$',
    r'^\s*Archive\s*$',
    r'^\s*Trending\s*$',
    r'^\s*Latest\s*$',
    r'^\s*Recent\s*$',
    r'^\s*Popular\s*$',
    r'^\s*Top\s*$',
    r'^\s*More\s*$',
    r'^\s*Next\s*$',
    r'^\s*Previous\s*$',
    r'^\s*Back\s*$',
    r'^\s*Continue\s*$',
    r'^\s*Skip\s*$',
    r'^\s*Settings\s*$',
    r'^\s*Profile\s*$',
    r'^\s*Account\s*$',
    r'^\s*Help\s*$',
    r'^\s*Support\s*$',
    r'^\s*FAQ\s*$',
    r'^\s*Terms\s*$',
    r'^\s*Privacy\s*$',
    r'^\s*Policy\s*$',
    r'^\s*Legal\s*$',
    r'^\s*Cookies\s*$',
    r'^\s*Teams\s*$',
    r'^\s*Blog\s*$',
    r'^\s*News\s*$',
    r'^\s*Events\s*$',
    r'^\s*Careers\s*$',
    r'^\s*Press\s*$',
    r'^\s*Investors\s*$',
    r'^\s*Latest\s+Stories\s*$',
    r'^\s*About\s+Medium\s*$',
    r'^\s*About\s+\w+\s*$',  # Generic "About <anything>"
    r'Home\s*\|\s*About\s*\|\s*Contact',
    r'Menu\s*\|\s*Search\s*\|\s*Login',
    r'Navigation\s*:.*?(?=\n\n|\.$)',
    r'Main\s+menu.*?(?=\n\n|\.$)',
    r'Breadcrumb.*?(?=\n\n|\.$)',
    r'You\s+are\s+here:.*?(?=\n\n|\.$)',
]

# Button and action patterns
BUTTON_PATTERNS = [
    r'Read\s+more',
    r'Learn\s+more',
    r'Download\s+now',
    r'Contact\s+us',
    r'Get\s+quote',
    r'Request\s+demo',
    r'Try\s+free',
    r'Start\s+trial',
    r'Book\s+demo',
    r'Schedule\s+call',
]

# OCR artifacts and noise
OCR_PATTERNS = [
    r'[|]{2,}',  # Multiple pipes
    r'[=]{3,}',  # Multiple equals
    r'[~]{3,}',  # Multiple tildes
    r'[_]{3,}',  # Multiple underscores
    r'\.{4,}',   # Multiple dots (4 or more)
    # Removed floating dots and commas patterns as they're too aggressive
]

# Non-ASCII character patterns (emojis, special characters)
NON_ASCII_PATTERNS = [
    r'[^\x00-\x7F]+',  # Non-ASCII characters
    r'[\u2600-\u26FF]',  # Miscellaneous Symbols (emojis)
    r'[\u2700-\u27BF]',  # Dingbats
    r'[\uFE00-\uFE0F]',  # Variation Selectors
    r'[\U0001F600-\U0001F64F]',  # Emoticons
    r'[\U0001F300-\U0001F5FF]',  # Misc Symbols and Pictographs
    r'[\U0001F680-\U0001F6FF]',  # Transport and Map
    r'[\U0001F1E0-\U0001F1FF]',  # Regional indicator symbols
]

# Pattern compilation flags for different categories
PATTERN_FLAGS = {
    'html': 0,  # No special flags
    'boilerplate': 're.IGNORECASE | re.DOTALL',
    'ad': 're.IGNORECASE | re.DOTALL',
    'nav': 're.IGNORECASE | re.MULTILINE',
    'button': 're.IGNORECASE | re.DOTALL',
    'ocr': 0,  # No special flags
    'non_ascii': 0,  # No special flags
}

# Navigation terms for exact line matching (case-insensitive)
NAV_TERMS = {
    'homepage', 'open in app', 'sign in', 'get started',
    'home', 'about', 'contact', 'menu', 'search', 'login',
    'register', 'subscribe', 'follow', 'following', 'archive',
    'trending', 'latest', 'recent', 'popular', 'top', 'more',
    'next', 'previous', 'back', 'continue', 'skip', 'settings',
    'profile', 'account', 'help', 'support', 'faq', 'terms',
    'privacy', 'policy', 'legal', 'cookies', 'teams', 'blog',
    'news', 'events', 'careers', 'press', 'investors',
    'latest stories', 'about medium', 'about ocd olly'
}

# Navigation prefixes to check for line starts
NAV_PREFIXES = [
    'about ', 'latest ', 'subscribe to ', 'follow us', 'like us',
    'share this', 'click here', 'read more', 'learn more'
]
