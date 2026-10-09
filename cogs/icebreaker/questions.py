BUILT_IN_QUESTIONS = [
  
{"id": "favorite_comfort_food",
"text": "What's a food that always makes you feel better?",},
  
{"id": "dream_vacation",
"text": "If you could travel anywhere tomorrow, where would you go?",},
  
{"id": "favorite_season",
"text": "What's your favorite season, and why?",},
  
{"id": "childhood_interest",
"text": "What's something you loved as a kid that you still enjoy?",},
  
{"id": "ideal_free_day",
"text": "What would your perfect day off look like?",},
  
{"id": "favorite_fictional_world",
"text": "Which fictional world would you most want to visit?",},
  
{"id": "favorite_sound",
"text": "What's a sound you find especially satisfying or comforting?",},
  
{"id": "new_skill",
"text": "What's a skill you'd love to learn?",},
  
{"id": "favorite_weather",
"text": "What's your ideal kind of weather?",},
  
{"id": "small_joy",
"text": "What's a small thing that can instantly improve your day?",},
  
{"id": "favorite_rewatch",
"text": "What's a show or movie you can watch over and over?",},
  
{"id": "dream_pet",
"text": "If you could have any animal as a pet, what would you choose?",},
  
{"id": "favorite_game",
"text": "What's a game you never get tired of playing?",},
  
{"id": "time_travel",
"text": "Would you rather visit the past or the future?",},
  
{"id": "favorite_book",
"text": "What's a book you think more people should read?",},
  
{"id": "perfect_room",
"text": "What would your dream room look like?",},
  
{"id": "music_mood",
"text": "What kind of music do you put on when you need a mood boost?",},
  
{"id": "unexpected_talent",
"text": "What's a random skill or fact you know that surprises people?",},
  
{"id": "favorite_snack",
"text": "What's your go-to snack?",},
  
{"id": "fictional_friend",
"text": "Which fictional character do you think you'd get along with best?",},
  
{"id": "dream_job",
"text": "If money weren't a factor, what job would you want to try?",},
  
{"id": "favorite_smell",
"text": "What's a smell you absolutely love?",},
  
{"id": "collecting",
"text": "If you started collecting something just for fun, what would it be?",},
  
{"id": "bucket_list",
"text": "What's one thing you'd really like to do someday?",},
  
{"id": "favorite_holiday",
"text": "What's your favorite holiday tradition?",},
  
{"id": "best_compliment",
"text": "What's a compliment you've received that stuck with you?",},
  
{"id": "alternate_life",
"text": "If you could try another person's job for a day, whose job would you pick?",},
  
{"id": "favorite_breakfast",
"text": "What does your ideal breakfast look like?",},
  
{"id": "revisit_memory",
"text": "What's a happy memory you'd love to experience again?",},
  
{"id": "everyday_invention",
"text": "What everyday invention are you especially grateful for?",},
  
{"id": "favorite_art_form",
"text": "What's your favorite way to be creative?",},
  
{"id": "ideal_superpower",
"text": "If you could have one superpower, what would it be?",},

{"id": "favorite_place",
"text": "What's a place where you feel especially comfortable?",},

{"id": "life_theme_song",
"text": "If your life had a theme song, what would it be?",},
  
{"id": "favorite_simple_pleasure",
"text": "What's an ordinary everyday thing you look forward to?",},
  
{"id": "dream_dinner_guest",
"text": "Who would you invite to a dream dinner, real or fictional?",},
  
{"id": "favorite_color",
"text": "Is there a color you especially love, and does it have a story?",},
  
{"id": "ideal_weekend",
"text": "What's your ideal way to spend a weekend?",},
  
{"id": "recent_discovery",
"text": "What's something new you've discovered recently and enjoyed?",},
  
{"id": "recommendation",
"text": "What's something you'd recommend everyone try at least once?",},
]

def get_builtin_questions() -> list[dict[str, str]]:
  return [question.copy() for question in BUILT_IN_QUESTIONS]
