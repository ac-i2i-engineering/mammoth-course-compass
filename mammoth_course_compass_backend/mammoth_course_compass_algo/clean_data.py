import pandas as pd
import re
from sklearn.preprocessing import MultiLabelBinarizer
from mammoth_course_compass_algo.models import Course, CourseRating
from datetime import datetime
from django.contrib.auth.models import User

# Define the expected columns
expected_columns = [
    'Timestamp', 'Email Address', 'Full Name', 'Class Year', 'Major', 'Additional Major 1', 
    'Additional Major 2', 'Domains of Interest', 'Do you have an idea (big or small)?',
    'What is your idea?', 'What stage are you at?', 'What role are you interested in taking on a team?',
    'What are your goals for the Lab?', 'Provide any additional information about yourself.',
    'Do you already have a team?', 'Has your team been registered?',
    'If your team has not registered enter your email below and we will send you the form.'
]

# Define the standard categories
domains_of_interest = ['arts', 'education', 'finance', 'healthcare', 'sustainability', 'social impact', 'technology']
goals_for_lab = ['learn about entrepreneurship and startups', 'build relationships', 'test my current idea', 'solve world problems', 'win i2i\'s support']
roles_interested = ['business strategy', 'engineering', 'financial']

def load_csv(file_path):
    """Load CSV file."""
    pd.set_option('display.max_columns', None)
    df = pd.read_csv(file_path)
    return df

def check_columns(df, expected_columns):
    """Check if all expected columns are present in the CSV."""
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if (missing_columns):
        raise ValueError(f"Missing columns in the CSV: {missing_columns}")

def clean_text(text):
    """Clean text fields."""
    if pd.isna(text):
        return ''
    text = text.strip().lower()  # Remove whitespace and convert to lowercase
    text = re.sub(r'\s*,\s*', ', ', text)  # Ensure consistent spacing
    return text

def apply_cleaning(df):
    """Apply cleaning to the relevant columns."""
    df['Domains of Interest'] = df['Domains of Interest'].apply(clean_text)
    df['What are your goals for the Lab?'] = df['What are your goals for the Lab?'].apply(clean_text)
    df['What role are you interested in taking on a team?'] = df['What role are you interested in taking on a team?'].apply(clean_text)

def split_and_match(df):
    """Split and match against standard categories."""
    df['Domains of Interest'] = df['Domains of Interest'].apply(lambda x: [domain for domain in domains_of_interest if domain in x])
    df['What are your goals for the Lab?'] = df['What are your goals for the Lab?'].apply(lambda x: [goal for goal in goals_for_lab if goal in x])
    df['What role are you interested in taking on a team?'] = df['What role are you interested in taking on a team?'].apply(lambda x: [role for role in roles_interested if role in x])

def create_binary_features(df):
    """Convert lists into binary encoded columns using MultiLabelBinarizer."""
    # Create binary features for Domains of Interest
    mlb_domains = MultiLabelBinarizer(classes=domains_of_interest)
    df_domains = pd.DataFrame(mlb_domains.fit_transform(df['Domains of Interest']), columns=mlb_domains.classes_, index=df.index)
    
    # Create binary features for Goals
    mlb_goals = MultiLabelBinarizer(classes=goals_for_lab)
    df_goals = pd.DataFrame(mlb_goals.fit_transform(df['What are your goals for the Lab?']), columns=mlb_goals.classes_, index=df.index)
    
    # Create binary features for Roles
    mlb_roles = MultiLabelBinarizer(classes=roles_interested)
    df_roles = pd.DataFrame(mlb_roles.fit_transform(df['What role are you interested in taking on a team?']), columns=mlb_roles.classes_, index=df.index)
    
    return df_domains, df_goals, df_roles

def concatenate_and_drop(df, df_domains, df_goals, df_roles):
    """Concatenate the original dataframe with the binary encoded features and drop original text columns."""
    df_profiles = pd.concat([df, df_domains, df_goals, df_roles], axis=1)
    df_profiles.drop(['Domains of Interest', 'What are your goals for the Lab?', 'What role are you interested in taking on a team?'], axis=1, inplace=True)
    return df_profiles

def filter_responses(df_profiles):
    """Filter to only include responses where 'Do you already have a team?' is 'No – match me with a team'."""
    return df_profiles[df_profiles['Do you already have a team?'] == 'No – match me with a team']

def create_user_profiles(df_filtered):
    """Create UserProfile instances from the filtered dataframe."""
    created_profiles = []  # Track successful creates
    failed_profiles = []   # Track failures
    
    for index, row in df_filtered.iterrows():
        try:
            user_profile = UserProfile(
                name=row['Full Name'],
                majors=f"{row['Major']}, {row['Additional Major 1']}, {row['Additional Major 2']}".strip(', '),
                interest_arts=row['arts'],
                interest_education=row['education'],
                interest_finance=row['finance'],
                interest_healthcare=row['healthcare'],
                interest_sustainability=row['sustainability'],
                interest_social_impact=row['social impact'],
                interest_technology=row['technology'],
                goal_learn=row['learn about entrepreneurship and startups'],
                goal_relations=row['build relationships'],
                goal_idea=row['test my current idea'],
                goal_problems=row['solve world problems'],
                goal_win_support=row['win i2i\'s support'],
                role_business=row['business strategy'],
                role_engineer=row['engineering'],
                role_finance=row['financial'],
                add_info=row['Provide any additional information about yourself.'],
                idea=row['What is your idea?']
            )
            user_profile.save()
            created_profiles.append(row['Full Name'])
        except Exception as e:
            failed_profiles.append((row['Full Name'], str(e)))
    
    # Print results
    print(f"Successfully created {len(created_profiles)} profiles")
    if failed_profiles:
        print(f"Failed to create {len(failed_profiles)} profiles:")
        for name, error in failed_profiles:
            print(f"- {name}: {error}")

def clean_and_create_users(file_path):
    """Main function to process the CSV file and create UserProfile instances."""
    df = load_csv(file_path)
    check_columns(df, expected_columns)
    apply_cleaning(df)
    split_and_match(df)
    df_domains, df_goals, df_roles = create_binary_features(df)
    df_profiles = concatenate_and_drop(df, df_domains, df_goals, df_roles)
    df_filtered = filter_responses(df_profiles)
    
    # Create UserProfile instances
    create_user_profiles(df_filtered)
    
    # Print the filtered and processed dataframe
    pd.set_option('display.max_columns', None)
    print(df_filtered)

def load_and_validate_csv(file_path):
    """Load CSV file and validate required columns."""
    expected_columns = [
        'Timestamp',
        'Rate the course overall from 1-5 (1 being worst and 5 being best)',
        'Rate the quality of instruction and teaching effectiveness',
        'Rate the relevancy/usefulness of course materials (1 being worst and 5 being best)',
        'Rate the manageability of assignments and workload (1 = very easy, 5 = very difficult)',
        'Rate the difficulty level of the course (1 being easiest and 5 being hardest)',
        'Rate how engaging, helpful the professor was (1 being least engaging and helpful and 5 being most engaging and helpful)',
        'How many hours a week do you spend on this course?',
        'What do you have to say about this course that is not portrayed through the general questions asked above?',
        'What course are you reviewing?',
        'Email Address'
    ]
    
    df = pd.read_csv(file_path)
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")
    return df

def clean_ratings_data(df):
    """Clean and validate rating values."""
    # Rename columns for easier handling
    column_mapping = {
        'Rate the course overall from 1-5 (1 being worst and 5 being best)': 'overall',
        'Rate the quality of instruction and teaching effectiveness': 'materials',
        'Rate the relevancy/usefulness of course materials (1 being worst and 5 being best)': 'course_content',
        'Rate the manageability of assignments and workload (1 = very easy, 5 = very difficult)': 'workload',
        'Rate the difficulty level of the course (1 being easiest and 5 being hardest)': 'difficulty',
        'Rate how engaging, helpful the professor was (1 being least engaging and helpful and 5 being most engaging and helpful)': 'professor',
        'What do you have to say about this course that is not portrayed through the general questions asked above?': 'review',
        'What course are you reviewing?': 'course_code',
        'Email Address': 'email'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Ensure ratings are within 1-5 range
    rating_columns = ['overall', 'materials', 'course_content', 'workload', 'difficulty', 'professor']
    for col in rating_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].clip(1, 5)
    
    return df

def create_course_ratings(df):
    """Create CourseRating instances from cleaned data."""
    created_count = 0
    failed_count = 0
    
    for _, row in df.iterrows():
        try:
            # Get or create user based on email
            user, _ = User.objects.get_or_create(
                email=row['email'],
                defaults={'username': row['email'].split('@')[0]}
            )
            
            # Get course (assuming it exists)
            course = Course.objects.get(code=str(row['course_code']))
            
            # Create course rating
            rating = CourseRating(
                user=user,
                course=course,
                materials=int(row['materials']),
                course_content=int(row['course_content']),
                workload=int(row['workload']),
                difficulty=int(row['difficulty']),
                professor=int(row['professor']),
                review=row['review'] if pd.notna(row['review']) else '',
            )
            
            # Calculate and set overall rating
            rating.overall = rating.calculate_overall_rating()
            rating.save()
            created_count += 1
            
        except Exception as e:
            print(f"Failed to create rating for {row['email']}: {str(e)}")
            failed_count += 1
    
    return created_count, failed_count