# Sambot
A Python [Flask](https://flask.palletsprojects.com/en/3.0.x/) chatbot built on-top of OpenAI's [chat completion](https://platform.openai.com/docs/api-reference/chat/create) and [embeddings](https://platform.openai.com/docs/api-reference/embeddings/create) API endpoints that produces truthful answers to a pre-determined set of questions, and engages in general conversation while taking on a personality similar to mine (the real Sam Morris). Check out the [live website](https://sammorris.ca) and try it out for yourself!

<img src="https://github.com/user-attachments/assets/7550fd69-5ca4-4932-8923-af7239b3ecb1" alt="screenshot1" width="500"/>

### Goals
When OpenAI's Chat-GPT model was first released to the public in November 2022, my friends and I were instantly amazed at it's capacity to hold a semi-rational conversation and use logic to solve problems. At the time, I didn't understand how it worked (and I still don't really,) but I knew that I would learn more about large-language models like Chat-GPT, and deploying a full-stack web application using Python, by using their API to build something unique. 

Some of my low-level goals for this project were to:
- Create a frontend GUI that communicates with a Python server;
- Stream data from the backend to the frontend to increase OpenAI's response speed;
- Prompt-engineer Chat-GPT to "act" like me;
- Stop Chat-GPT from spreading [false information](https://en.wikipedia.org/wiki/Hallucination_(artificial_intelligence));
- Keep track of user sessions to remember conversations;
- Generate consistent responses to important questions;

### Design
Much of the design is aimed at reducing hallucinations from Chat-GPT, so that it doesn't lie about my job experience, background, etc. This was accomplished (with a pretty good consistency) by only pulling relevant information needed to answer the specific question asked by the user. 

First, the user question is rephrased by Chat-GPT 4o based on the current context of the conversation. This helps with the embedding search because important keywords are included in the sentence that the user may not have included, which are then used to search for similar knowledge in the embeddings. For example, the user's question could be something like: "tell me more!", but the rephrased question might look like: "the user wants to know more about your job experience at Emburse Inc."

Second, the rephrased user question is turned into an embedding that gets compared to other embeddings of sentences with true information about me. Any embeddings of true sentences about me that are closer than some distance to the rephrased user question embedding are included in the system prompt to send to Chat-GPT 4o.

Last, a file containing system instructions for Chat-GPT 4o is included alongside the embedded sentences and form the final system prompt that is sent to OpenAI's API. Below is a simple diagram illustrating this process.

![image](https://github.com/user-attachments/assets/ed73eac8-438c-4db2-ad31-28c517a5a17e)

### Acknowledgements
I am grateful to [Avery Suzuki](https://averysuzuki.com/selected-work) for his significant contribution to this project. Throughout the entire process, has has helped me with prompt-engineering, website design, and just generally telling me when my ideas are bad. Thanks Ave!
