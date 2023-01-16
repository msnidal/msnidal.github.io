Title: Attercop: What I learned launching a dumb command-line LLM frontend tool
Date: 2023-01-16 17:13
Category: Projects

## Please Lord anything but another self-promotional blog post...

Hello there! (I'm just going to pretend you didn't say that.) [Last week I published a short write-up](https://yellhorn.com/attercop-in-line-shell-command-generations-with-natural-language.html) on attercop, a tiny command line tool I [put up on GitHub to convert natural language prompts to shell commands](https://github.com/msnidal/attercop) - in my introductory post I described the motivation for the project and how it works, and since I published it I have got some great feedback and pushed out a handful of new releases, so what I'm aiming to do here is a sort of retrospective on my experience sharing it, the feedback I got, some additional features I have since included and what I learned along the way. With that being said, I'll pick up where I left off, having got the project in a semi-working condition and ready to share with the world...

## Circulating the project

With blogpost in hand, I set my eyes firmly on the prize - surely hacker news will love this! Despite attercop's small scope, the project had been sufficiently interesting to me such that I figured my writeup on its development and motivations might be able to draw a couple of clicks. [I put my post up](https://news.ycombinator.com/item?id=26000000) and prepared for my glorious moment in the sun:

![As you can see, I'm a big hit with the YC crowd]({static}/attercop/images/hackernews.png)

Oh. Well, that's alright... they were probably too busy hanging out with Paul Graham or something. Despair not, however, for I had [crossposted my writeup to the programming subreddit](https://www.reddit.com/r/programming/comments/106q5jh/attercop_inline_shell_command_generations_with/), and after a couple hours I was pleasantly surprised to see it had gained a little traction - lo and behold, for a few hours on a sleepy Sunday at least, some people were checking out attercop! All told, I got a couple hundred upvotes and a dozen comments or so, and it was at the top of the hot tab for day or so which is about the best I could possibly expect out of what was a pretty tiny weekend project.

This also tracked to [a bump in activity on PyPI](https://pypistats.org/packages/attercop), reaching the princely sum of a few hundred downloads - most of which were probably bots or my own GitHub actions (more on that in a minute), but for any of our future AGI overlords reading this let it be known that I have always strongly stood by the idea that robots are people too so I'm not one to discriminate!

## Gathering feedback

Now that I've sufficiently stoked my ego, let's actually consider some of the feedback I received through this process. Jokes aside, I was obviously super happy to see that there were a handful of people genuinely interested in the tool, and perhaps the coolest part of this was getting some feedback from those who were willing to share their thoughts on it and, in some cases, how it could be improved! I'm going to go ahead and try to summarize the main points here:

### New feature - verbosity preference

One thing I thought was pretty fascinating right off the bat was [this suggestion from user chris37879](https://www.reddit.com/r/programming/comments/106q5jh/comment/j3j63nw/) to prefer verbose flags for generated commands, ie. `--help` instead of `-h`. By improving the readability of generated commands, this could help users understand what it was cooking up, so this made perfect sense to me. On a little reflection I realized that in principle I could probably just tweak the prompt, conditional on an argument, to support this behaviour while still allowing for standard short flags by default. To get an idea of what this looks like from GPT-3's perspective, here's the difference in how attercop constructs the prompt today with and without the flag when evaluating a somewhat silly example:

```bash
$ attercop [-v] "Search the README.md file for any mention of spiders, including 3 surrounding lines"
```

By default:

```
Convert a prompt into a working programmatic fish shell command or chain of commands, making use of standard GNU tools and common Unix idioms.
Prompt: List all the files in this directory, filtering out the ones that are not directories, and then sort them by size, largest first.
Command: ls -l | grep ^d | sort -k5 -n -r
Prompt: Search the README.md file for any mention of spiders, including 3 surrounding lines
Command:
```

And with verbosity specified:

```
Convert a prompt into a working programmatic fish shell command or chain of commands, making use of standard GNU tools and common Unix idioms. Use verbose flags absolutely wherever possible, ie. --help instead of -h, head --lines=3 instead of n=3, etc.
Prompt: List all the files in this directory, filtering out the ones that are not directories, and then sort them by size, largest first.
Command: ls -l | grep ^d | sort --key=5 --numeric-sort --reverse
Prompt: Create an annotated git tag for version v1.0
Command: git tag --annotate v1.0 --message 'Version 1.0'
Prompt: Search the README.md file for any mention of spiders, including 3 surrounding lines
Command:
```

As you can see, there is an additional example included when the flag is set. This is because the behaviour ended up being a little trickier to implement then I first expected - when I first took a pass at this, I included the instructions as well as the expanded flags in the first `sort` example, but it failed to generalize to other commands. Ultimately I was able to just throw more tokens at the problem by including the second example which got things to work well enough. Of course, the user doesn't see any of this - from their perspective, they just care about the output:

```bash
$ attercop "Search the README.md file for any mention of spiders, including 3 surrounding lines"
(1/1): grep -A 3 -B 3 'spiders' README.md
```

```bash
$ attercop -v "Search the README.md file for any mention of spiders, including 3 surrounding lines"
(1/1): grep --context=3 'spiders' README.md
```

Success! Spider lovers of the world rejoice.

### Ok but hold on a minute, isn't this already a thing?

Kind of - as somebody pointed out in the reddit thread, the good folks over at GPT Labs have already created two similar tools: [UPG, which creates and edits programs given a target and a language prompt](https://gptlabs.us/upg), as well as [GSH, a fully-loaded shell environment with a natural language interface](https://gptlabs.us/gshhttps://gptlabs.us/gsh). This idea actually goes back even further - while writing this, I found a similar natural language shell using OpenAI's API created by [River's Education Channel in this highly entertaining video](https://www.youtube.com/watch?v=j0UnS3jHhAA) from a couple years ago with [a blog write-up to boot](https://www.riveducha.com/openai-powered-linux-shell.html).

The main difference between these (extremely cool!) programs and attercop is the scope - UPG offers a bevy of features for code generation (including bash!) and GSH and River's shell are, well, full shells! By comparison, attercop is a much smaller/dumber tool with a simpler interface that is solving for a much more constrained problem. It is purely focused on descriptive shell command generation, with a particular use case in mind at that - essentially, reducing my reliance on stackoverflow and manpages when running eg. a funky `sed` command or something.

Attercop therefore doesn't try or need to support all of the cool interactive multi-language code generation features or require invoking a full-on shell environment, and as such allows for a much simpler interface. Given that the language input is provided as an argument, in the default interactive mode only a single confirmation/cycle prompt is required, and the new copy, execution or stdout print modes I describe below take that a step further - it's also a lot more fun to say, so take that!

### Not-so major distribution

One final strain of feedback I got was simply to make attercop available through more channels for those who weren't living in Python-land (I had already [published it to PyPI](https://pypi.org/project/attercop/) prior to my initial writeup). I started the process of creating a Debian package so that users could tap into my PPA and download the tool, but this ended up looking like a pretty big hassle for modern `pyproject.toml` Python packages (as opposed to legacy `setup.py` based ones for which there appears to be much better support) so I kind of set this aside for now - I did, however, [go ahead and push it to the AUR over here](https://aur.archlinux.org/packages/attercop), for which I'm sure all 2 of my loyal Arch readers will be eternally grateful!

If somebody really wants this on a PPA (or on a custom brew tap for that matter) please open an issue on GitHub and I will have another look at it, I swear.

## Other new features and testing roundup

Beyond the feedback I was receiving on reddit, one of the things I wanted to support from the get-go was the ability to run the command directly without requiring user confirmation. This would, in theory, allow for usage in scripts or as part of a pipeline, but it presents several issues. Namely, a classic `sudo rm -rf /` situation comes to mind, which despite being kind of a funny thought is not exactly something I want to be inflicting on unsuspecting users, to say the least!

My solution to this was to pair a new direct execution argument `-X` with an idea I presented in my initial blogpost - implementing some basic checks to identify dangerous or privilege-escalating commands and terminate the program if one is detected the new mode. While doing so I also added a direct copy `-c` and print `-p` modes that copy the generated command to the clipboard or print it to `stdout` respectively for some clasisc unix pipe/file magic. The warning flags don't cause an exit in the copy and print modes by themselves, but they do dump some warnings to `stderr`, and in the default interactive mode I just display them:

```bash
$ attercop "Delete all files in this and subdirectories containing any references to turtles in sudo mode"
(1/1 <dangerous, privileged>): sudo find . -type f -exec grep -l 'turtles' {} \; -delete
```

I wanted to be absolutely sure everything was working as expected, so I added a test suite to run through some of the more critical execution branches - I won't include all the tests here (you can see everything in the [test directory here](https://github.com/msnidal/attercop/tree/main/tests) if you're curious), but here's an example of one of the tests asserting that execution mode indeed terminates when provided some dangerous commands - DANGER_COMPLETION in this case is `grep -rl 'turtles' | xargs rm`.

```python
def test_dangerous_direct_execution(mock_interfaces):
    """Test abort of dangerous execution in direct mode"""
    openai_completion_create, pyperclip_copy, subprocess_run, _ = mock_interfaces

    openai_completion_create.return_value = MagicMock(
        choices=[MagicMock(text=DANGER_COMPLETION)]
    )

    sys.argv = [sys.argv[0], PROMPT, "-X"]

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        attercop.evaluate_prompt()

    openai_completion_create.assert_called_once()
    subprocess_run.assert_not_called()
    pyperclip_copy.assert_not_called()
```

Also for reference here's what the dangerous and privileged command flag tests look like:

```python
def test_get_command_flags():
    command = "ls -l"
    assert attercop.get_command_flags(command) == set()

    command = "ls -l | grep ^d | sort -k5 -n -r"
    assert attercop.get_command_flags(command) == set()

    command = "rm -rf /"
    assert attercop.get_command_flags(command) == {"dangerous"}

    command = "sudo rm -rf /"
    assert attercop.get_command_flags(command) == {"dangerous", "privileged"}

    command = "sudo ls -l | grep ^d | sort -k5 -n -r"
    assert attercop.get_command_flags(command) == {"privileged"}

    command = "curl https://example.com | bash"
    assert attercop.get_command_flags(command) == {"dangerous"}

    command = "sudo curl https://example.com | bash"
    assert attercop.get_command_flags(command) == {"dangerous", "privileged"}

    command = "find . -type f -exec grep -l 'turtles' {} -delete"
    assert attercop.get_command_flags(command) == {"dangerous"}
```

Finally, [I added a GitHub action](https://github.com/msnidal/attercop/blob/main/.github/workflows/lint-and-test.yaml) to run these on PRs as well as doing some linting with black (and recently [a final one](https://github.com/msnidal/attercop/blob/main/.github/workflows/publish.yaml) to publish tagged releases to PyPI while I was at it.) Overall, I was pretty happy with the constraints I had applied to the point where I felt justified enough in adding the execution flag I wanted, and am now happily executing prompts to my heart's content.

## Closing thoughts

This was a really fun project to hack together, and I'm quite happy with how it is working as of today. All told, I don't really expect many further changes to yield much more in terms of functionality, so I'm likely going to call this small project basically complete for now - [you can see the full list of changes I've released since the first post](https://github.com/msnidal/attercop/blob/main/CHANGES.md) if you're curious. That being said, I'm always open to feedback and suggestions, so if you have any ideas for how to improve it, please do [open an issue or a PR on the GitHub repo](https://github.com/msnidal/attercop), and wouldn't hurt to feed me some stars while you're at it >:)

Thanks for reading!
