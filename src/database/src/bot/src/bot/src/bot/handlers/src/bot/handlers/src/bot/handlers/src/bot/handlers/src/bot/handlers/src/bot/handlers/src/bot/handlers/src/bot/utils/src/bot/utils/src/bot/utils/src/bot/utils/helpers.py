"""
Helper functions for Habesha Dating Bot
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Language codes
LANG_EN = 'en'
LANG_AM = 'am'

# Available languages
LANGUAGES = {
    LANG_EN: 'English',
    LANG_AM: 'አማርኛ'
}

# Translation dictionary
TRANSLATIONS = {
    # Welcome & Registration
    'welcome': {
        LANG_EN: "👋 *Welcome to Habesha Dating Bot!*\n\nLet's create your profile. What's your full name?",
        LANG_AM: "👋 *እንኳን ወደ ሐበሻ የትዳር ቦት መጡ!*\n\nመገለጫዎን መፍጠር እንጀምር። ሙሉ ስምዎ ማን ነው?"
    },
    'age_prompt': {
        LANG_EN: "How old are you? (18-100)",
        LANG_AM: "ዕድሜዎ ስንት ነው? (18-100)"
    },
    'invalid_age': {
        LANG_EN: "Please enter a valid age between 18 and 100.",
        LANG_AM: "እባክዎ ትክክለኛ ዕድሜ ከ18 እስከ 100 ያስገቡ።"
    },
    'gender_prompt': {
        LANG_EN: "What's your gender?",
        LANG_AM: "ጾታዎ ምንድን ነው?"
    },
    'male': {
        LANG_EN: "👨 Male",
        LANG_AM: "👨 ወንድ"
    },
    'female': {
        LANG_EN: "👩 Female",
        LANG_AM: "👩 ሴት"
    },
    'location_prompt': {
        LANG_EN: "Where do you live? (City)",
        LANG_AM: "የሚኖሩበት ከተማ የት ነው?"
    },
    'region_prompt': {
        LANG_EN: "Which region? (e.g., Addis Ababa, Oromia, Amhara)",
        LANG_AM: "የሚኖሩበት ክልል የት ነው? (ለምሳሌ፦ አዲስ አበባ፣ ኦሮሚያ፣ አማራ)"
    },
    'ethnicity_prompt': {
        LANG_EN: "What is your ethnicity?",
        LANG_AM: "ብሄረሰብዎ ምንድን ነው?"
    },
    'ethnicity_amhara': {
        LANG_EN: "Amhara",
        LANG_AM: "አማራ"
    },
    'ethnicity_oromo': {
        LANG_EN: "Oromo",
        LANG_AM: "ኦሮሞ"
    },
    'ethnicity_tigray': {
        LANG_EN: "Tigray",
        LANG_AM: "ትግራይ"
    },
    'religion_prompt': {
        LANG_EN: "What is your religion?",
        LANG_AM: "ሃይማኖትዎ ምንድን ነው?"
    },
    'religion_orthodox': {
        LANG_EN: "Orthodox",
        LANG_AM: "ኦርቶዶክስ"
    },
    'religion_muslim': {
        LANG_EN: "Muslim",
        LANG_AM: "ሙስሊም"
    },
    'religion_protestant': {
        LANG_EN: "Protestant",
        LANG_AM: "ፕሮቴስታንት"
    },
    'skip': {
        LANG_EN: "Skip",
        LANG_AM: "ዝለል"
    },
    'education_prompt': {
        LANG_EN: "What is your education level?",
        LANG_AM: "የትምህርት ደረጃዎ ምንድን ነው?"
    },
    'occupation_prompt': {
        LANG_EN: "What is your occupation?",
        LANG_AM: "ሙያዎ ምንድን ነው?"
    },
    'goal_prompt': {
        LANG_EN: "What are you looking for?",
        LANG_AM: "ምን ዓይነት ግንኙነት ነው የሚፈልጉት?"
    },
    'goal_marriage': {
        LANG_EN: "💍 Marriage",
        LANG_AM: "💍 ጋብቻ"
    },
    'goal_dating': {
        LANG_EN: "💕 Dating",
        LANG_AM: "💕 ጓደኝነት"
    },
    'goal_friendship': {
        LANG_EN: "🤝 Friendship",
        LANG_AM: "🤝 ወዳጅነት"
    },
    'goal_notsure': {
        LANG_EN: "🤔 Not sure",
        LANG_AM: "🤔 እርግጠኛ አይደለሁም"
    },
    'bio_prompt': {
        LANG_EN: "Tell us about yourself (max 500 chars):",
        LANG_AM: "ስለራስዎ ይንገሩን (እስከ 500 ቁምፊዎች)፦"
    },
    'photo_prompt': {
        LANG_EN: "📸 Please upload 3-5 clear photos of yourself.\n\n⚠️ No group photos or downloaded images!",
        LANG_AM: "📸 እባክዎ 3-5 ግልጽ የሆኑ የራስዎን ፎቶዎች ይላኩ።\n\n⚠️ የቡድን ፎቶዎች ወይም የወረዱ ምስሎች አይፈቀዱም!"
    },
    'referral_prompt': {
        LANG_EN: "Do you have a referral code? (type 'skip' to skip)",
        LANG_AM: "የማጣቀሻ ኮድ አለዎት? ('skip' በማለት ይዝለሉት)"
    },
    'registration_complete': {
        LANG_EN: "✅ *Registration Complete!*\n\nYour profile is under review. You'll be notified when approved. Thank you! 🙏",
        LANG_AM: "✅ *ምዝገባ ተጠናቋል!*\n\nመገለጫዎ በግምገማ ላይ ነው። ሲጸድቅ እናሳውቅዎታለን። እንደጠበቁ እናመሰግናለን! 🙏"
    }
}

def get_text(key: str, lang: str = LANG_EN, **kwargs) -> str:
    """Get translated text for a given key and language"""
    if key in TRANSLATIONS:
        text = TRANSLATIONS[key].get(lang, TRANSLATIONS[key][LANG_EN])
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text
    return key

def validate_age(age: int) -> bool:
    """Validate age is within acceptable range"""
    return 18 <= age <= 100

def format_date(date_str: str) -> str:
    """Format date string to readable format"""
    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date.strftime('%Y-%m-%d')
    except:
        return date_str[:10]