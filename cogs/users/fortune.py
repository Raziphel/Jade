# Discord
from discord.ext.commands import command, Cog, ApplicationCommandMeta, cooldown, BucketType
from discord import Member, User, ApplicationCommandOption, ApplicationCommandOptionType
# Additions
from random import choice
from time import monotonic

# Utils
import utils

class fortune(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.YesorNo = ([
            "Yeah, why not...",
            "Yes, but that's gross!",
            "No. Your a loser! >;c",
            "I can't answer stupidity.",
            "Yeah, but that's really stupid!",
            "No, you nasty furry~",
            "Eww wtf. Hell no!",
            "Only a homosexual would ask that.",
            "I was told to say No.",
            "I was told to say Yes.",
            "Wtf?  Yeah fuck no.",
            "Oh fuck.  Fuck Yes.",
            "Yeah, but you need jesus...",
            "No x100!  That's horrible.",
            "Why ofcourse you gayfur~",
            "Yeah no.  100% not!",
            "Wow, hell no! settle down there f slur!",
            "No, thank you. But that's gross.",
            "Yeah, but your probably gonna get a disease...",
            "Are you gay? Then maybe...",
            "Yes, but you'll get cancer",
            "Yes but your lover will harass you.",
            "Oh my fucking god, yes!",
            "Yes, but only if it's tuesday.",
            "What are you talking about? Of course not!?",
            "The answer is yes, but your gay af for asking.",
            "Never going to happen! Ever!",
            "Nope, never!",
            "Yes, but get drunk af first!",
            "Only if you eat ass while doing it.",
            "Probably, yeah?",
            "Oh baby.  You better believe it.",
            "It's a high likelihood!",
            "Yikes, how about no.",
            "Yoooooo, hell no, settle down.",
            "Omfg, yeah that's a big fat no.",
            "Wtf, yeah why not.",
            "C'mon you already know that's a no.",
            "You ask too many questions, but no.",
            "Sometimes...",
            "Without a doubt that's a no.",
            "Hell no, to the no.",
            "Yeah for sure.",
            "Shut the hell up, ofcourse.",
            "God damn it, NO."
            "Absolutely, if you enjoy bad decisions!",
            "Yes, but only if you wear a chicken suit!",
            "No way, José! Get real.",
            "Only if you're a professional idiot.",
            "Yes, but you'll regret it immediately!",
            "No, not even with a million dollars!",
            "Yikes, that sounds like a bad time.",
            "Sure, if you're trying to get kicked out!",
            "Yes, but only if you’re prepared for chaos.",
            "Definitely yes, but only on a full moon!",
            "I can't even with that question.",
            "Oh heck no, that’s just wrong.",
            "For sure, but only if it's a dare!",
            "Nope, that's a hard pass.",
            "Yes, but you're definitely going to jail.",
            "LOL, yes, but I won’t be your alibi!",
            "Why yes, if you like to live dangerously!",
            "No, but I’ll sell you popcorn to watch!",
            "Yes, but bring your own parachute.",
            "No, unless you're looking for trouble.",
            "Totally, if you enjoy life in the fast lane!",
            "Yes, but you might lose a limb.",
            "Yes, but only if it involves ice cream!",
            "Sure, if you’re okay with being embarrassed.",
            "What are you smoking? That's a no.",
            "Yes, but it’s a one-way ticket to regret.",
            "No, and don’t ask me again!",
            "Yeah, but only if it’s at 3 AM.",
            "Definitely not, that’s just weird.",
            "Why not, if you like clowns?",
            "Yes, but you’re gonna need therapy after.",
            "Only if you promise to take me with you.",
            "No way, not on my watch!",
            "Sure, just don't tell your mom!",
            "Absolutely not! What were you thinking?",
            "Yes, if you have a good lawyer.",
            "No, and that's final.",
            "Yup, if you're feeling lucky!",
            "No, not even if I get a million bucks.",
            "Yes, but only if it's taco night!",
            "Sure, if you want to be a meme.",
            "Nope, try again later.",
            "Yeah, but only after a shot of tequila!",
            "What even is that? No!",
            "Yes, but I can't guarantee safety!",
            "No, because I value my sanity.",
            "Sure, but be prepared for chaos!",
            "Yeah, only if it involves dancing!",
            "Nah, that's a total buzzkill.",
            "Of course! But I’ll judge you.",
            "Yes, but I won’t be responsible for your choices.",
            "No, and don’t you dare think about it!",
            "Absolutely, but only if you wear a clown wig.",
            "Why not, if you're trying to win a Darwin Award!",
            "Sure, if you don't mind public humiliation.",
            "Nope, that’s a big fat no.",
            "Only if it includes pizza!",
            "Yes, but you'll probably cry.",
            "Definitely not! Go home!",
            "Yes, but it’s a one-time deal.",
            "No, because I’m not your therapist.",
            "Only if you’re trying to ruin your reputation.",
            "Why yes, but only if you bring snacks.",
            "No, because that’s just not right.",
            "Sure, but only if it’s on a dare!",
            "Yes, but you might wake up regretting it!",
            "Nope, not a chance!",
            "Yes, if you promise to make it hilarious.",
            "No, but I’ll support you from a distance!",
            "Totally yes, but I’ll be laughing the whole time.",
            "Yes, but don’t come crying to me later.",
            "For sure, if you want to be a trendsetter!",
            "No, because that sounds illegal.",
            "Yes, but it might involve some spicy consequences.",
            "Nah, that’s just too cringe for me.",
            "Yes, if you're ready for an adventure!",
            "Only if you want to become an internet sensation.",
            "No, and I’m serious!",
            "Yes, if you can dance like nobody’s watching!",
            "Nope, not happening!",
            "Sure, just make sure to film it.",
            "Yes, but only if you don’t mind the chaos.",
            "Definitely not, you weirdo!",
            "Yes, but don’t blame me for the aftermath.",
            "No, and I mean it!",
            "Absolutely yes, if you want a wild story.",
            "Yes, but be ready to explain yourself!",
            "No, because that’s just wrong on so many levels.",
            "Why yes, if you’re into bad ideas!",
            "Sure, but you'll probably regret it tomorrow.",
            "Yup, if you can handle the consequences.",
            "No, that's a hard no.",
            "Yes, but you might end up on a watchlist.",
            "No, but I’ll cheer you on from afar!",
            "Yes, if you want to spice up your life!",
            "No way, you’ll embarrass yourself!",
            "Of course yes, but it’s a bad idea.",
            "Yeah, if you want to live on the edge!",
            "No, because I care about your safety!",
            "Absolutely yes, if you want a wild ride!",
        ])


    @command(aliases=['8ball', 'fortune', 'Ask', 'Fortune'],
            application_command_meta=ApplicationCommandMeta(
            options=[
                ApplicationCommandOption(
                    name="question",
                    description="The question you wish to ask!",
                    type=ApplicationCommandOptionType.string,
                    required=True,
                ),
            ],
        ),
    )
    async def ask(self, ctx, question):
        """Ask the bot a yes or no question."""
        contents = question.split()
        total_words = len(question.split())
        response = "I don't understand that question~"

        for word in contents:
            if word.lower() in ["am", "will", "does", "should", "can", "are", "do", "is", "did", "was"]:
                response = choice(self.YesorNo)

        await ctx.send(embed=utils.Embed(desc=f"**Q:** __{question}__\n\n**A:** {response}"))











def setup(bot):
    x = fortune(bot)
    bot.add_cog(x)