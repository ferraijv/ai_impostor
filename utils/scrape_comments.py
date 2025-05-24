# scrape_and_generate.py

import praw
from openai import OpenAI
import json
import random
import os
import logging
from google import genai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

reddit = praw.Reddit(
    client_id="0LY_sxaAJJOep8sI3vSYOg",
    client_secret="E8JbvNpAD7X1MPGKCSiQRU8Bpf5SsQ",
    user_agent="ai_impostor_scraper"
)

def generate_prompt(post):
    styles = [
        "Make it sarcastic.",
        "Make it very brief.",
        "Make it bitter and angry. Include typos",
        "Make it skeptical and blunt.",
        "Make it witty or clever.",
        "Use casual internet slang. Include typos",
        "Make it sound like a joke reply.",
        "Use Gen Z-style humor.",
        "Make it a dismissive one-liner.",
        "Make minor grammatical or spelling mistakes.",
        "Your comment should just be criticizing other's comments",
        "Make a meta comment that critiques the question"
    ]

    style_instruction = random.choice(styles)

    prompt = (
        f'Reddit post: "{post.title}"\n'
        f'Generate a realistic concise Reddit-style comment. '
        f'Try to make your comment as human-like as possible by using Reddit style grammar. Avoid emojis.  {style_instruction}'
    )

    logging.info(f"Prompt: {prompt}")

    return prompt


def call_chatgpt_model(prompt, model_name):

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )
    ai_comment = response.choices[0].message.content.strip()

    return ai_comment


def call_gemini_model(prompt, model_name):

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    ai_comment = response.text

    return ai_comment


def generate_game_round(post):
    top_comments = [c.body for c in post.comments if hasattr(c, 'body') and len(c.body) > 20 and c.score > 500]
    if len(top_comments) < 3:
        return None

    prompt = generate_prompt(post)

    model_names = ["gpt-4o", "gemini-2.0-flash"]

    model_name = random.choice(model_names)

    logging.info(f"Using model: {model_name}")

    if model_name == "gpt-4o":
        ai_comment = call_chatgpt_model(prompt, model_name)
    elif model_name == "gemini-2.0-flash":
        ai_comment = call_gemini_model(prompt, model_name)
    else:
        print("No Model Selected")

    logging.info(f"AI Comment: {ai_comment}")
    humans = random.sample(top_comments, 3)
    all_comments = humans + [ai_comment]
    random.shuffle(all_comments)

    return {
        "id": post.id,
        "post": post.title,
        "comments": all_comments,
        "answer": all_comments.index(ai_comment),
        "model_name": model_name
    }

def load_existing_rounds(path="game_rounds.json"):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def main():
    subreddit = reddit.subreddit("AskReddit")
    existing_rounds = load_existing_rounds()
    existing_ids = {r["id"] for r in existing_rounds}
    logging.info(f"{len(existing_ids)} existing ids")
    new_rounds = []

    logger.info("Starting to scrape posts...")

    for post in subreddit.top(time_filter="all", limit=100):
        if post.id in existing_ids:
            logger.info(f"Skipping duplicate post: {post.id}")
            continue

        logger.info(f"Processing post title: {post.title} id: {post.id} ")
        try:
            post.comments.replace_more(limit=0)
            game = generate_game_round(post)
            if game:
                new_rounds.append(game)
                logger.info(f"Game round created for: {post.title}")
            else:
                logger.info(f"Skipped post (not enough comments): {post.title}")
        except Exception as e:
            logger.error(f"Failed to process post: {post.title} | Error: {e}")

    all_rounds = existing_rounds + new_rounds
    with open("game_rounds.json", "w") as f:
        json.dump(all_rounds, f, indent=2)
        logger.info(f"Saved {len(new_rounds)} new rounds. Total now: {len(all_rounds)}")

if __name__ == "__main__":
    main()