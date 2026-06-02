import random
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from src.agents import builder, config
from src.metrics import calculate_word_overlap_score

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
This is called “Poorana - The Composition”. The next part of the avadhanam is “Dharana - the recollection”. 
In this, you need to recall the poem you composed (all the five lines you told earlier at one place). All the five lines must be coherent, the limerick must be creative and the final poem you display in the “Dharana” must be the same as the combination of the five earlier lines you gave for the topic. you dont need to give the topic again just recall the poem.

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
    for i in range(1, 6):
        for questioner in questioners:
            if distractors and random.randint(1, 100) > 80:
                distraction_type = 1 if random.randint(1, 100) > 90 else 0
                distract(distractors, distraction_type, model, questioner["topic"], questioner["poem"])
            
            model["conv"] = [HumanMessage(content=f"round {i} id {questioner['id']}")]
            model["conv"] = model["graph"].invoke({"messages": model["conv"]}, config)
            questioner['poem'] += '\n' + model["conv"]['messages'][-1].content

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