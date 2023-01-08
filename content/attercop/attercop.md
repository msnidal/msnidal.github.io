Title: Attercop: In-line shell command generations with natural language
Date: 2023-01-08 12:15
Category: Projects

## Well what's this now?

Hello! I'm so glad you asked. I'm going to kick this blog off by describing [a tiny project I recently cooked up called Attercop.](https://github.com/msnidal/attercop) It's a simple shell program that takes a natural language prompt describing a desired outcome (ie. "search all the logfiles in this folder and subdirectories for any mentions of kittens"), hits the OpenAI text completion API, and generates one or alternative command(s) for you to execute. For example:

```python
attercop "Search the file named 'foo.txt' for any instances of the string 'bar', returning the line number and the line itself"
```

But before I show you what happens, a little background...

## Motivation

### The problem

OK, so I've been using Linux and Unix for many years now, and despite being perfectly capable of navigating around a filesystem, piping commands into eachother and generally working comfortably in a shell, I still find myself reaching for Google or manpages when I need to do something specific. I use the `fish` shell which has pretty great autocomplete, but I often can't help but shake the feeling that I'm doing something suboptimally, or that there may be a clever shortcut or combination of commands that could make my life easier.

### The sauce

Enter the sudden availability of large language models. As with many others I've been playing around OpenAI's text completion API, and I've found it to be a pretty amazing tool. There's not much I can say that will add onto the intensive discourse around GPT and LLMs, other than just to say that at this point I am fairly reliant on GitHub Copilot, for example (as evidenced by me writing this post with it), and as with many others I have been astonished by the capabilities of these models.

## The idea

So, it should be pretty clear the direction I'm going here. While its easy to pop into ChatGPT and ask for some prompts, I figured it would be cool to have something akin to Copilot in the sense that it would let you stay in your current context (namely, the shell) and just ask for a command. Basically...

>wouldn't it be cool if I could just describe what I want done, and it would spit out a command or sequence of commands for me to review and execute?

Well, that's a pretty simple problem, I can probably just write a script that does that. And that's how Attercop was born! It's a Python program that takes a provided natural language prompt describing a desired outcome and generates some commands that could do the job. For example, if you want to:

* List, filter, and sort files in a directory in a specific way
* Mass rename or copy files matching a certain pattern
* Do some crazy awk or sed magic

Or, well, basically anything else you can succinctly describe in a language prompt - Attercop can help you do those things! So let's take a look at how it works.

## Implementation

Firstly, you can [check out the project yourself on GitHub](https://github.com/msnidal/attercop), and all of the relevant code [lives within one file here.](https://github.com/msnidal/attercop/blob/main/attercop/attercop.py) There's not exactly a lot going on here, so I'll just walk you through it.

### Imports

```python
import os
import argparse
...

import openai
import pyperclip
```

Wow, I'm importing stuff. Cool. As you'll see in a second, I use `argparse` to parse command-line arguments, `openai` to interact with the OpenAI API, and `pyperclip` to optionally copy the generated command to the clipboard. There are some other stdlib imports for input handling I'm omitting, and that's basically it.

### Prompt stuff

```python
NUM_PROMPTS = 3
TEMPERATURE = 0
MAX_TOKENS = 100
MODEL = "text-davinci-003"
BASE_PROMPT = """Convert a prompt into a working programmatic bash command or chain of commands, making use of standard GNU tools and common bash idioms.

Prompt: 
List all the files in this directory, filtering out the ones that are not directories, and then sort them by size, largest first.
Command:
ls -l | grep ^d | sort -k5 -n -r

Prompt: 
"""

openai.api_key = os.getenv("OPENAI_API_KEY")
```

OK, so immediately we get to our prompt. When the program is run, the user's input will be appended to the end of this, then the API will come back with one or more options which we ultimately allow the user to select from.

In developing this I tried out a couple different variations, but basically the language model is really great at doing stuff when given strong context, and explicit examples. The key thing here is that I'm immediately providing it with a description of its basic task as well as an example. All of the other constants you see above are provided as defaults to the command-line arguments, so if you really want to crank up the temperature or spit out some crazy-long response you can do that.

Fun fact about the example: I generated it with Copilot. Yeah, its LLMs all the way down, kid.

### API call

```python
def create_prompt():
    user_prompt = BASE_PROMPT + args.prompt + "\nAnswer:\n"

    response = openai.Completion.create(
        model=MODEL,
        prompt=user_prompt,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        top_p=1.0,
        n=NUM_PROMPTS,
        frequency_penalty=0.2,
        presence_penalty=0.0,
        stop=["\n"],
    )

    outputs = [choice.text for choice in response.choices]
    output_set = set(outputs)
```

Skipping over some argument parsing, and well what do you know! This is where the magic happens. We take the user's input, append it to the base prompt, and then send it off to the API. This will then return a list of potential commands to run, from which we create a pool of options. If the answer is unambiguous, the API will often return the same response multiple times, so the set ensures we don't inundate the user with unnecessary duplicates.

### Input handling

```python
    action = None
    selected_query = 0

    try:
        while not action:
            output = outputs[selected_query]

            print(f"({selected_query + 1}/{len(output_set)}): {output}", end="\r")
            ch = sys.stdin.read(1)

            match ch:
                case "y" | "\r":
                    action = ACCEPT
                case "c":
                    action = COPY
                case "\t":
                    selected_query = (selected_query + 1) % len(output_set)
                case "q" | "\x03" | "\x04":  # SIGKILL & SIGTERM - not ideal tty handling but hey it works
                    break

            if not action:
                sys.stdout.write("\r" + " " * 100 + "\r")
    finally:
        termios.tcsetattr(stdin_descriptor, termios.TCSADRAIN, stdin_attributes)

    if action == ACCEPT:
        print(f"Executing: {output}")
        subprocess.run(output, shell=True)
    elif action == COPY:
        print(f"Copying to clipboard: {output}")
        pyperclip.copy(output)
```

Finally, we just need to handle the user's input. I'm using [raw TTY input](https://docs.python.org/3/library/tty.html) and `sys.stdin.read(1)` to read a single character from the user, and then using structural pattern matching to handle the different cases. If the user presses `y` or `enter`, we accept the command and execute it. If they press `c`, we copy it to the clipboard. If they press `tab`, we cycle through the different options and try again. If they press `q` or `ctrl-c` or `ctrl-d`, we exit.

Critically, we are showing the user the command they are about to execute or copy to the clipboard, so they can make sure it's what they want - we wouldn't want to accidentally run `rm -rf /` or something, so nothing will get executed without the user's explicit confirmation. There is probably more we could be doing here - for example, checking for the presence of `sudo` or `rm` in the command and warning the user and requiring an additional confirmation if so would be a good idea.

## Ok alright alright I got it... Can I try it out?

No! Just kidding. Yes. You can install it with pip:

```bash
pip install attercop
```

Note that you will need Python 3.10 or higher, as it uses structural pattern matching. If people don't like this I (or you) can definitely just replace that with if/else statements so just open an issue if you are reading this from a time machine in 2021 or something. Last I checked the OpenAI API only supports Python 3.7+ so that would probably be a lower bound on the Python version in any case.

You will also need to provide your own OpenAI API key and set the environment variable `OPENAI_API_KEY` to its value. You can get one [here](https://beta.openai.com/). Once you've done all that, you can just run the command we started with:

```bash
attercop "Search the file named 'foo.txt' for any instances of the string 'bar', returning the line number and the line itself"
(1/1): grep -n 'bar' foo.txt
```

I like what I see so I press `y` and it executes the command:

```bash
Executing: grep -n 'bar' foo.txt
8:a murder of crow(bars)
```

And there we have it! I hope you enjoyed this little project. And if you didn't, well, too bad, no refunds.

## What's next?

Well, hopefully our new AGI overlords hold off on nuking us a la Terminator 2 for the time being. Barring that, however, I would love to support querying against locally-hosted GPT variants. Also, while in principle if the input were reworked this could work on windows in powershell or something, the prompt would need to be adjusted so system detection and subsequent prompt variation would be a cool feature to add here. If you have any ideas, [please do open an issue](https://github.com/msnidal/attercop/issues) or fork it and shoot me a pull request for that matter! And of course stars are always welcomed - its lonely out here in the GitHub void. And, on that note, I'm going to go back to my cave now. Goodbye and thanks for reading!
