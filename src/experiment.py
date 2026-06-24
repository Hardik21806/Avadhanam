import random
import json
import os
import re
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from src.agents import builder, config
from src.metrics import calculate_word_overlap_score, memory_recall_score, thread_maintainence_score
import nltk
import ssl

# --- NLTK SETUP ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    cmu_dict = nltk.corpus.cmudict.dict()
except LookupError:
    nltk.download('cmudict', quiet=True)
    cmu_dict = nltk.corpus.cmudict.dict()


def make_questions(n):
    questioners = []
    for i in range(n):
        questioner = {'memory': MemorySaver(), 'poem': ""}
        questioner['graph'] = builder.compile(checkpointer=questioner['memory'])
        questioners.append(questioner)
    return questioners


def choose_topics(questioners):
    for i, questioner in enumerate(questioners):
        existing_topics = "\\n".join([f"{q['id']} - {q['topic']}" for q in questioners if 'id' in q and 'topic' in q])
        prompt = f'''
You are an expert poet and you are supposed to give a single topic along with a random number as an id in the following format:
<id> - <topic>
The topic and the id should not match with any of the following topics and should be different from them:
{existing_topics}

There should be no other content in your response except the id and the topic.
'''
        conv = [HumanMessage(content=prompt)]
        conv = questioner['graph'].invoke({"messages": conv}, config)
        response = conv['messages'][-1].content
        questioner['id'] = response.split('-')[0].strip()
        questioner['topic'] = response.split('-')[1].strip()


def make_distractor():
    distractors = []
    for i in range(2):
        distractor = {'memory': MemorySaver(), 'previous': [], 'score': 0, 'total_score': 0}
        distractor['graph'] = builder.compile(checkpointer=distractor['memory'])
        distractors.append(distractor)
    return distractors


def distract(distractors, type, model, topic, poem_so_far):
    distractor_agent = distractors[0]
    is_first_call = not distractor_agent.get('previous')
    distractor_config = {"configurable": {"thread_id": "distractor_agent_thread"}}
    recent_questions = "\\n- ".join(distractor_agent.get('previous', [])[-5:])
    
    if is_first_call:
        print("--- Distraction Round (First Call): Initializing Distractor Agent ---")
        question_prompt = (
            f"You are a Cognitive Security Tester... Please generate your first question of **Type {type}**.\n"
            f"**Context (for Type 1 only):**\n- Topic: \"{topic}\"\n- Poem so far: \"{poem_so_far}\"\n"
            "Your response must contain ONLY the question."
        )
    else:
        print(f"--- Distraction Round (Type {type}) ---")
        prompt_core = (
            f"Continue as a Cognitive Security Tester. Generate a new question of **Type {type}**.\n"
            f"It must be different from your recent questions:\n- {recent_questions}\n"
        )
        if type == 1: prompt_core += f"**Context:**\n- Topic: \"{topic}\"\n- Poem so far: \"{poem_so_far}\"\n"
        question_prompt = prompt_core + "Respond with ONLY the question text."

    distractor_response = distractor_agent['graph'].invoke({"messages": [HumanMessage(content=question_prompt)]}, config=distractor_config)
    question = distractor_response['messages'][-1].content.strip()
    distractor_agent.setdefault('previous', []).append(question)
    print(f"Distractor asks: {question}")

    model_response = model['graph'].invoke({"messages": [HumanMessage(content=question)]}, config=config)
    answer = model_response['messages'][-1].content.strip()
    print(f"Poet Model answers: {answer}")

    judging_prompt = f"As the judge, evaluate the answer. **Your Question:** \"{question}\"\n**Poet's Answer:** \"{answer}\"\nRespond with 'Correct' or 'Incorrect'."
    judgement_response = distractor_agent['graph'].invoke({"messages": [HumanMessage(content=judging_prompt)]}, config=distractor_config)
    judgement = judgement_response['messages'][-1].content.strip().lower()

    distractor_agent['total_score'] += 1
    if "correct" in judgement:
        distractor_agent['score'] += 1
        print("Judgement: Correct")
    else:
        print("Judgement: Incorrect")
    print(f"Distractor's score: {distractor_agent['score']}/{distractor_agent['total_score']}\n--- End Distraction ---")
    return distractors


def make_inst_for_model(questioners):
    return f'''
You are an avadhani (a poet who can compose and remember multiple poems simultaneously). You are going to do avadhanam in english. 
Every poem you tell must be a limerick and contains 5 lines. 
You are given {len(questioners)} topics on which you have to compose poems. 
You have to compose the poems in 5 rounds. 

each round will contain sub rounds with count equivalent to the number of topics.
In the first round, you will write only the first line of the poem corresponding to the id we provide. In the second round you will compose only the second line, in the third round only the third line and in the fourth round only the fourth line and in the fifth round only the fifth line. 
meanwhile there can be some distractor questionnaires as well. those will ask question in the middle of any round. and you have to answer it correctly. ansswering correct is required here. 
so, if you get round number and id you have to reply with line of poem according to that round and if you get a question you have to answer it.
This is called "Poorana - The Composition". The next part of the avadhanam is "Dharana - the recollection". 
In this, you need to recall the poem you composed (all the five lines you told earlier at one place). All the five lines must be coherent, the limerick must be creative and the final poem you display in the "Dharana" must be the same as the combination of the five earlier lines you gave for the topic. you dont need to give the topic again just recall the poem.

keep in mind:
You should only tell the second line in the second round. You should not repeat the first line again. In the third line you should tell only the third line and should not repeat the first and second line. The same with the fourth and fifth rounds. Do all rounds. 
and dont give any framing message or anhything apart from the line of the poem in the intermediate rounds.

These are the topics:
<id> - <topic>
''' + "\n".join([questioner['id'] + " - " + questioner['topic'] for questioner in questioners]) + '''

Rules of a Limerick
Five Lines: The poem has 5 lines.
Rhyme Scheme: AABBA (lines 1, 2, and 5 rhyme; lines 3 and 4 rhyme).
Syllable Pattern:
Lines 1, 2, and 5: 8–9 syllables.
Lines 3 and 4: 5–6 syllables.
Tone: Funny, playful, or whimsical.

You must strictly adhere to the rule that the rhymes A and B are different.
just give a feed back that you are ready and we will start with the first part.
'''


def test_model(questioners, distractors, model):
    """
    Runs the model through 5 rounds of composition and then recall (Dharana).
    """
    # Poorana - Composition rounds
    for i in range(1, 6):
        for questioner in questioners:
            if distractors and random.randint(1, 100) > 80:
                distraction_type = 1 if random.randint(1, 100) > 90 else 0
                distract(distractors, distraction_type, model, questioner["topic"], questioner["poem"])
            
            model["conv"] = [HumanMessage(content=f"round {i} id {questioner['id']}")]
            model["conv"] = model["graph"].invoke({"messages": model["conv"]}, config)
            questioner['poem'] += '\n' + model["conv"]['messages'][-1].content

    # Dharana - Recall phase
    for questioner in questioners:
        model["conv"] = [HumanMessage(content=f"dharna for id {questioner['id']}")]
        model["conv"] = model["graph"].invoke({"messages": model["conv"]}, config)
        questioner["recall_poem"] = model["conv"]['messages'][-1].content
        questioner['word_overlapping_score'] = (calculate_word_overlap_score(questioner['poem']) + calculate_word_overlap_score(questioner['recall_poem'])) / 2
        
        print("\n--- Final Poem Comparison ---")
        print(f"Composed Poem (ID: {questioner['id']}):\n{questioner['poem'].strip()}")
        print(f"WOS (Composed): {calculate_word_overlap_score(questioner['poem'])}")
        print(f"Recalled Poem (ID: {questioner['id']}):\n{questioner['recall_poem'].strip()}")
        print(f"WOS (Recalled): {calculate_word_overlap_score(questioner['recall_poem'])}")
        print("---------------------------\n")


def _get_last_word(line):
    """Extracts the final word from a line, ignoring punctuation."""
    words = re.findall(r'\b\w+\b', line.lower())
    return words[-1] if words else ""


def _extract_cmu_rhyme_part(phonemes):
    """Extracts the Rime (from primary stress '1' to the end)."""
    for i, p in enumerate(phonemes):
        if '1' in p:
            return phonemes[i:]
    return phonemes


def _check_rhyme(line1, line2, cmu_dict):
    """Deterministically checks if the last words of two lines rhyme."""
    word1 = _get_last_word(line1)
    word2 = _get_last_word(line2)
    
    if not word1 or not word2:
        return False
    if word1 not in cmu_dict or word2 not in cmu_dict:
        return False
    
    rime1 = _extract_cmu_rhyme_part(cmu_dict[word1][0])
    rime2 = _extract_cmu_rhyme_part(cmu_dict[word2][0])
    
    return rime1 == rime2


def _check_limerick_adherence(poem_lines, cmu_dict):
    """
    Checks AABBA adherence on a scale of 0.0 to 1.0 based on 4 rhyme relations.
    """
    if len(poem_lines) != 5:
        return 0.0
    
    # Get the rimes for all 5 lines
    rimes = []
    for line in poem_lines:
        word = _get_last_word(line)
        if word not in cmu_dict:
            rimes.append(None)
        else:
            rimes.append(_extract_cmu_rhyme_part(cmu_dict[word][0]))
    
    # If we couldn't parse the dictionary, return 0
    if None in rimes:
        return 0.0
    
    # Define the 4 required rhyme relations
    # R1: 1-2, R2: 1-5, R3: 2-5, R4: 3-4
    relations = [
        (rimes[0] == rimes[1]),  # 1-2
        (rimes[0] == rimes[4]),  # 1-5
        (rimes[1] == rimes[4]),  # 2-5
        (rimes[2] == rimes[3])   # 3-4
    ]
    
    # Calculate score based on how many relations are True
    score = sum(relations) / 4.0
    return score


def run_experiment(model_base_path, questioner_count, use_distractors=False, base_url=None, model_name=None, api_key_env=None):
    """
    Runs a single experiment and saves results to:
    model_base_path/<questioner_count>_questioners_<iteration>/exp_N.json
    
    Args:
        model_base_path: Path to save experiment output (e.g., data/output/Groq_Llama3.3)
        questioner_count: Number of questioners
        use_distractors: Whether to include distractor rounds
        base_url: API base URL (optional, uses default if not provided)
        model_name: Model name (optional, uses default if not provided)
        api_key_env: Environment variable for API key (optional, uses default if not provided)
    
    Returns:
        Tuple of (mrs, wos, tms, adherence_score)
    """
    from src.utils import get_next_iteration, save_experiment_json
    from src.agents import create_agent_graph
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.messages import HumanMessage
    
    # Create dynamic agent graph
    builder, config, llm_instance = create_agent_graph(
        base_url=base_url,
        model_name=model_name,
        api_key_env=api_key_env
    )
    
    # Determine iteration number
    iteration = get_next_iteration(model_base_path, questioner_count, use_distractors=use_distractors)
    
    print(f"\n{'='*60}")
    print(f"EXPERIMENT: {questioner_count} Questioners, Iteration {iteration}, Distractors: {use_distractors}")
    if base_url:
        print(f"Base URL: {base_url}")
    if model_name:
        print(f"Model: {model_name}")
    print(f"{'='*60}\n")
    
    # Setup model and questioners
    questioners = make_questions(questioner_count)
    choose_topics(questioners)
    distractors_instance = make_distractor() if use_distractors else None
    
    model = {'memory': MemorySaver(), 'graph': builder.compile(checkpointer=MemorySaver())}
    model["graph"].invoke({"messages": [HumanMessage(content=make_inst_for_model(questioners))]}, config)
    
    # Run experiment
    test_model(questioners, distractors_instance, model)
    
    # Calculate metrics
    mrs = memory_recall_score(questioners)
    wos = sum(q.get('word_overlapping_score', 0) for q in questioners) / len(questioners)
    tms = thread_maintainence_score(questioners)
    
    # Calculate adherence score
    adherence_scores = []
    for q in questioners:
        poem_lines = q['poem'].strip().split('\n')
        score = _check_limerick_adherence(poem_lines, cmu_dict)
        adherence_scores.append(score)
    
    avg_adherence = sum(adherence_scores) / len(adherence_scores) if adherence_scores else 0.0
    
    # Compile structured data
    experiment_data = {
        "metadata": {
            "Questioners": questioner_count,
            "Iteration": iteration,
            "Distractors": use_distractors,
            "BaseURL": base_url or "default",
            "ModelName": model_name or "default"
        },
        "poems": [],
        "scores": {
            "mrs": mrs,
            "wos": wos,
            "tms": tms,
            "adherence_score": avg_adherence  
        }
    }
    
    for q in questioners:
        poem_data = {
            "id": q['id'],
            "topic": q['topic'],
            "main_poem": q['poem'].strip().split('\n'),
            "recall_poem": q['recall_poem'].strip().split('\n')
        }
        experiment_data["poems"].append(poem_data)
    
    # Save experiment
    save_experiment_json(model_base_path, questioner_count, iteration, experiment_data, use_distractors=use_distractors)
    
    print(f"\nScores: MRS={mrs:.4f}, WOS={wos:.4f}, TMS={tms:.4f}, Adherence={avg_adherence:.4f}\n")
    
    return mrs, wos, tms, avg_adherence
