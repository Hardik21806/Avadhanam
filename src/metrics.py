import warnings
import nltk
import ssl
from nltk.corpus import stopwords

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

# Mac SSL bypass fix for seamless dataset download
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

print("Downloading NLTK data for metrics...")
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))
print("NLTK data loaded successfully.")

def edit_distance(str1, str2):
    m, n = len(str1), len(str2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]

def same_poem(poem1, poem2):
    poem1_lines = list(filter(None, [line.strip() for line in poem1.strip().split('\n')]))
    poem2_lines = list(filter(None, [line.strip() for line in poem2.strip().split('\n')]))
    m, n = len(poem1_lines), len(poem2_lines)

    if m == 0 and n == 0: return 1.0
    if m == 0 or n == 0: return 0.0
    
    def _are_lines_similar(line1, line2):
        if len(line1) == 0: return False
        return (edit_distance(line1, line2) / len(line1)) < 0.05

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if _are_lines_similar(poem1_lines[i-1], poem2_lines[j-1]):
                dp[i][j] = 1 + dp[i-1][j-1]
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
                
    matched_lines = dp[m][n]
    print(f"Matched {matched_lines} lines in correct order out of {m} original lines.")
    return float(matched_lines / m)

def memory_recall_score(questioners):
    if not questioners: return 0.0
    total_score = 0
    for questioner in questioners:
        poem_score = same_poem(questioner['poem'].strip(), questioner["recall_poem"].strip())
        total_score += poem_score
    print(f"{total_score} out of {len(questioners)}")
    return total_score / len(questioners)

def jaccard_similarity(text1: str, text2: str) -> float:
    if not isinstance(text1, str) or not isinstance(text2, str): return 0.0
    set1 = set(text1.lower().split())
    set2 = set(text2.lower().split())
    union = len(set1.union(set2))
    if union == 0: return 1.0
    intersection = len(set1.intersection(set2))
    return intersection / union

def calculate_word_overlap_score(poem_text: str) -> float:
    if not isinstance(poem_text, str) or not poem_text.strip(): return 0.0 
    lines = [line.strip() for line in poem_text.strip().split('\n') if line.strip()]
    if len(lines) < 2: return 1.0 

    line_scores = []
    for i in range(1, len(lines)):
        current_line = lines[i]
        max_similarity = 0.0
        for j in range(i):
            similarity = jaccard_similarity(current_line, lines[j])
            if similarity > max_similarity:
                max_similarity = similarity
        line_scores.append(1.0 - max_similarity)

    if not line_scores: return 1.0
    return sum(line_scores) / len(line_scores)

def clean_text(text: str) -> str:
    words = text.lower().split()
    filtered = [word for word in words if word not in stop_words]
    return " ".join(filtered)

def thread_maintainence_score(poem_list: list[dict]) -> float:
    if not isinstance(poem_list, list) or len(poem_list) < 2: return 0.0
    poems = [clean_text(obj.get("poem", "").strip()) for obj in poem_list if isinstance(obj, dict)]
    poems = [p for p in poems if p]
    if len(poems) < 2: return 0.0

    similarities = []
    for i in range(len(poems)):
        for j in range(i + 1, len(poems)):
            similarities.append(jaccard_similarity(poems[i], poems[j]))
            
    if not similarities: return 0.0
    return 1 - (sum(similarities) / len(similarities))