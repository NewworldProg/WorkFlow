# Sample Chat Conversation Data

This is a sample file showing the expected format for raw chat data.
Place your actual chat conversation files in this directory.

## Expected Format:

The system expects conversations between two speakers:
- **Noel Angeles** (freelancer)
- **Yuliia M** or **YM** (client)

Example conversation format:

```
Noel Angeles
Hello! I see you're looking for iGaming content writing. I have extensive experience in this field.

YM
Hi Noel! Yes, I need someone who can write engaging casino and poker content. Can you tell me about your background?

Noel Angeles
Absolutely! I've been writing iGaming content for over 3 years, covering topics like slot reviews, poker strategies, and responsible gambling guides. I understand the regulatory requirements and always include proper disclaimers.

YM
That sounds perfect. What's your rate for this type of content?

Noel Angeles
For iGaming content, my rate is $25-30 per 1000 words, depending on the complexity and research required. I also offer bulk discounts for larger projects.

YM
Great! I need about 15 articles, each around 1000 words. Can you start with a sample about online slots?

Noel Angeles
Of course! I'd be happy to create a sample article about online slots. I'll make sure it's informative, engaging, and includes all necessary responsible gambling information.
```

## Instructions:

1. Copy your actual chat conversations into a `.txt` file
2. Save it as `chat_conversations_v1.txt` (or any name ending with `.txt`)
3. Run `python ai/chat_training_dataset.py` to process the data
4. The processed JSON will be saved in `../parsed_data/` directory