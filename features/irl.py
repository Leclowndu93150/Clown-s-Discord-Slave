from discord.ext import commands
import random
import hashlib
import discord


def get_love_score(person1, person2):
    person1 = person1.strip().lower()
    person2 = person2.strip().lower()
    ascii_sum1 = sum(ord(char) for char in person1)
    ascii_sum2 = sum(ord(char) for char in person2)
    combined = f"{person1}{person2}{random.random()}"
    hashed = hashlib.sha256(combined.encode()).hexdigest()
    hash_nums = sum(int(c, 16) for c in hashed if c.isdigit())
    length_factor = abs(len(person1) - len(person2)) + 1
    common_letters = set(person1) & set(person2)
    common_factor = len(common_letters) * 7
    random_noise = random.randint(0, 50)
    base_score = (ascii_sum1 + ascii_sum2 + hash_nums + common_factor + random_noise) / length_factor
    percentage_score = base_score % 100
    multiplier = random.uniform(0.5, 1.5)
    final_score = int(percentage_score * multiplier) % 101
    return final_score


class Irl(commands.Cog):

    @commands.hybrid_command(name="kharchi", aliases=["kharcher", "nacer"], help="Gives all of Kharchi's Roles",
                             brief="Kharchi")
    async def kharchi(self, ctx):
        await ctx.send("""
        Bien cordialement,   
        Nacer Kharchi
        Administrateur informatique du bâtiment A
        Administrateur ENT des lycée Voillaume
        Administrateur GAR des lycées Voillaume ͏‌ 
        Administrateur Pronote des lycées Voillaume
        Coordonnateur numérique du LGT Voillaume
        Référent numérique des lycées Voillaume
        Référent Pix des lycées Voillaume
        Enseignant référent TALENS/CPES
        """)

    @commands.hybrid_command(name="love_compatiblity", aliases=["love", "compatibility"],
                             help="Gives the love compatibility between two people", brief="Love Compatibility")
    async def love_compatiblity(self, ctx, person1: str, person2: str):
        score = get_love_score(person1, person2)
        await ctx.send(f"Love Compatibility between {person1} and {person2} is {score}%")
