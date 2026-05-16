#!/usr/bin/env python3
"""Ingest the 10 books for Phase-6 expansion.

Each entry contains:
  • url      — exact Aozora URL (matched to the user's list, in order)
  • id       — kebab-case slug for public/books/<id>/
  • level    — beginner|intermediate|advanced (per user's tier classification)
  • title_*  — title in ja, fr, en, zh
  • author_* — author name in each language (ja in kanji, others romanized)
  • summary_*— 1-2 sentence summary in each language

These metadata follow the same shape as STARTER_BOOKS in aozora.py so we can
reuse the existing `process_one()` machinery without modification.

Run from inside the gengo-library project root:

    python3 ingest_phase6.py
"""
import sys
from pathlib import Path

# Reuse the aozora pipeline
sys.path.insert(0, str(Path(__file__).parent))
from aozora import process_one  # noqa: E402

REPO_ROOT = Path(__file__).parent
WORK_DIR = REPO_ROOT / ".epub-cache"
WORK_DIR.mkdir(exist_ok=True)


BOOKS = [
    # 1 - 銀河鉄道の夜 (Miyazawa Kenji) — intermediate
    {
        'url': 'https://www.aozora.gr.jp/cards/000081/files/456_15050.html',
        'id': 'ginga-tetsudo-no-yoru',
        'level': 'intermediate',
        'title_ja': '銀河鉄道の夜',
        'title_fr': 'Train de Nuit dans la Voie Lactée',
        'title_en': 'Night on the Galactic Railroad',
        'title_zh': '银河铁道之夜',
        'author_ja': '宮沢賢治',
        'author_fr': 'Miyazawa Kenji',
        'author_en': 'Miyazawa Kenji',
        'author_zh': '宫泽贤治',
        'summary_fr': "Un garçon solitaire voyage à travers les étoiles dans un train mystérieux et rencontre l'âme de son ami disparu. Conte poétique et métaphysique.",
        'summary_en': "A lonely boy travels through the stars on a mysterious train and meets the soul of his lost friend. A poetic, metaphysical tale.",
        'summary_zh': "一个孤独的男孩乘坐神秘列车穿越星空，遇见已逝朋友的灵魂。一个诗意而形而上学的故事。",
    },
    # 2 - 山月記 (Nakajima Atsushi) — intermediate
    {
        'url': 'https://www.aozora.gr.jp/cards/000119/files/624_14544.html',
        'id': 'sangetsuki',
        'level': 'intermediate',
        'title_ja': '山月記',
        'title_fr': 'Le Récit de la Lune sur la Montagne',
        'title_en': 'The Moon over the Mountain',
        'title_zh': '山月记',
        'author_ja': '中島敦',
        'author_fr': 'Nakajima Atsushi',
        'author_en': 'Nakajima Atsushi',
        'author_zh': '中岛敦',
        'summary_fr': "Un poète raté se transforme en tigre et raconte sa déchéance à un ancien ami. Méditation sur l'orgueil et l'art.",
        'summary_en': "A failed poet transforms into a tiger and tells the story of his downfall to an old friend. A meditation on pride and art.",
        'summary_zh': "一位失败的诗人变成了老虎，向旧友讲述自己的堕落。关于傲慢与艺术的沉思。",
    },
    # 3 - 羅生門 (Akutagawa) — intermediate
    {
        'url': 'https://www.aozora.gr.jp/cards/000879/files/127_15260.html',
        'id': 'rashomon',
        'level': 'intermediate',
        'title_ja': '羅生門',
        'title_fr': 'Rashōmon',
        'title_en': 'Rashōmon',
        'title_zh': '罗生门',
        'author_ja': '芥川龍之介',
        'author_fr': 'Akutagawa Ryūnosuke',
        'author_en': 'Akutagawa Ryūnosuke',
        'author_zh': '芥川龙之介',
        'summary_fr': "À l'ombre de la porte de Rashōmon dans le Kyoto médiéval, un serviteur sans emploi rencontre une vieille femme et fait un choix moral inattendu.",
        'summary_en': "In the shadow of the Rashōmon gate in medieval Kyoto, an unemployed servant meets an old woman and makes an unexpected moral choice.",
        'summary_zh': "在中世纪京都的罗生门阴影下，一位失业仆人遇到一位老妇人，做出了意想不到的道德选择。",
    },
    # 4 - 高瀬舟 (Mori Ōgai) — intermediate
    {
        'url': 'https://www.aozora.gr.jp/cards/000129/files/691_15352.html',
        'id': 'takasebune',
        'level': 'intermediate',
        'title_ja': '高瀬舟',
        'title_fr': 'La Barque sur la Takase',
        'title_en': 'The Boat on the Takase River',
        'title_zh': '高濑舟',
        'author_ja': '森鴎外',
        'author_fr': 'Mori Ōgai',
        'author_en': 'Mori Ōgai',
        'author_zh': '森鸥外',
        'summary_fr': "Un fonctionnaire escorte un prisonnier condamné à l'exil sur une barque ; leur conversation pose la question de l'euthanasie et de la compassion.",
        'summary_en': "An official escorts a prisoner sentenced to exile on a small boat; their conversation raises questions of euthanasia and compassion.",
        'summary_zh': "一名官员押送一位被判流放的犯人乘船而行；他们的对话引发了关于安乐死与同情的思考。",
    },
    # 5 - 二十四の瞳 (Tsuboi Sakae) — intermediate
    {
        'url': 'https://www.aozora.gr.jp/cards/001875/files/57856_63624.html',
        'id': 'nijushi-no-hitomi',
        'level': 'intermediate',
        'title_ja': '二十四の瞳',
        'title_fr': 'Vingt-quatre Prunelles',
        'title_en': 'Twenty-Four Eyes',
        'title_zh': '二十四只眼睛',
        'author_ja': '壺井栄',
        'author_fr': 'Tsuboi Sakae',
        'author_en': 'Tsuboi Sakae',
        'author_zh': '壶井荣',
        'summary_fr': "Une jeune institutrice d'une petite île japonaise accompagne ses douze élèves à travers les tourments de la guerre et de l'après-guerre.",
        'summary_en': "A young teacher on a small Japanese island accompanies her twelve students through the turmoils of war and post-war life.",
        'summary_zh': "日本一个小岛上的年轻教师，陪伴她的十二个学生经历战争与战后的动荡岁月。",
    },
    # 6 - 蟹工船 (Kobayashi Takiji) — beginner (par classement du user)
    {
        'url': 'https://www.aozora.gr.jp/cards/000156/files/1465_16805.html',
        'id': 'kanikosen',
        'level': 'beginner',
        'title_ja': '蟹工船',
        'title_fr': 'Le Bateau-Usine',
        'title_en': 'The Crab Cannery Ship',
        'title_zh': '蟹工船',
        'author_ja': '小林多喜二',
        'author_fr': 'Kobayashi Takiji',
        'author_en': 'Kobayashi Takiji',
        'author_zh': '小林多喜二',
        'summary_fr': "À bord d'un bateau-usine de pêche au crabe dans les mers glaciales du nord, des ouvriers exploités finissent par se révolter. Roman prolétarien classique.",
        'summary_en': "On a crab cannery ship in the freezing northern seas, exploited workers eventually rise up in rebellion. A classic of proletarian literature.",
        'summary_zh': "在北方冰冷海域的蟹工船上，被剥削的工人最终奋起反抗。无产阶级文学经典之作。",
    },
    # 7 - こころ (Sōseki) — advanced
    {
        'url': 'https://www.aozora.gr.jp/cards/000148/files/773_14560.html',
        'id': 'kokoro',
        'level': 'advanced',
        'title_ja': 'こころ',
        'title_fr': 'Le Pauvre Cœur des Hommes',
        'title_en': 'Kokoro',
        'title_zh': '心',
        'author_ja': '夏目漱石',
        'author_fr': 'Natsume Sōseki',
        'author_en': 'Natsume Sōseki',
        'author_zh': '夏目漱石',
        'summary_fr': "Un étudiant noue une amitié étrange avec un homme solitaire surnommé Sensei. Une exploration profonde de la culpabilité, de l'amitié et de la modernité japonaise.",
        'summary_en': "A student forms a strange friendship with a solitary man known as Sensei. A profound exploration of guilt, friendship, and Japanese modernity.",
        'summary_zh': "一位学生与一位名为先生的孤独男子建立起奇特的友谊。对内疚、友情与日本现代性的深刻探索。",
    },
    # 8 - 吾輩は猫である (Sōseki) — advanced
    {
        'url': 'https://www.aozora.gr.jp/cards/000148/files/789_14547.html',
        'id': 'wagahai-wa-neko-de-aru',
        'level': 'advanced',
        'title_ja': '吾輩は猫である',
        'title_fr': 'Je suis un chat',
        'title_en': 'I Am a Cat',
        'title_zh': '我是猫',
        'author_ja': '夏目漱石',
        'author_fr': 'Natsume Sōseki',
        'author_en': 'Natsume Sōseki',
        'author_zh': '夏目漱石',
        'summary_fr': "Un chat sarcastique observe et commente la vie d'un professeur médiocre et de ses amis. Satire mordante de la société japonaise en pleine modernisation.",
        'summary_en': "A sardonic cat observes and comments on the life of a mediocre teacher and his friends. A biting satire of modernizing Japanese society.",
        'summary_zh': "一只讽刺的猫观察并评论一位平庸教师和他朋友们的生活。对日本现代化社会的辛辣讽刺。",
    },
    # 9 - 人間失格 (Dazai) — advanced
    {
        'url': 'https://www.aozora.gr.jp/cards/000035/files/301_14912.html',
        'id': 'ningen-shikkaku',
        'level': 'advanced',
        'title_ja': '人間失格',
        'title_fr': 'La Déchéance d\'un Homme',
        'title_en': 'No Longer Human',
        'title_zh': '人间失格',
        'author_ja': '太宰治',
        'author_fr': 'Dazai Osamu',
        'author_en': 'Dazai Osamu',
        'author_zh': '太宰治',
        'summary_fr': "Les carnets d'un homme incapable de comprendre les autres êtres humains, qui sombre dans l'alcool, la drogue et le désespoir. Une des œuvres les plus sombres du Japon moderne.",
        'summary_en': "The notebooks of a man unable to understand other human beings, who sinks into alcohol, drugs, and despair. One of modern Japan's darkest works.",
        'summary_zh': "一个无法理解他人的男人留下的笔记，他逐渐沉沦于酒精、毒品与绝望之中。日本现代文学最阴郁的作品之一。",
    },
    # 10 - 小僧の神様 (Shiga Naoya) — advanced
    # Note: the URL given (001095/42886_23088.html) is Shiga Naoya's "Kozō no Kamisama"
    # which the user listed as "小説の神様". The correct title is 小僧の神様
    # (The Apprentice's God) — assuming this is what was meant.
    {
        'url': 'https://www.aozora.gr.jp/cards/001095/files/42886_23088.html',
        'id': 'kozo-no-kamisama',
        'level': 'advanced',
        'title_ja': '小僧の神様',
        'title_fr': "Le Dieu de l'Apprenti",
        'title_en': "The Apprentice's God",
        'title_zh': '小僧的神',
        'author_ja': '志賀直哉',
        'author_fr': 'Shiga Naoya',
        'author_en': 'Shiga Naoya',
        'author_zh': '志贺直哉',
        'summary_fr': "Un jeune apprenti rêve de manger des sushis trop chers pour lui. Un client compatissant lui offre ce festin, mais la rencontre laisse un sentiment trouble. Court récit emblématique du style de Shiga.",
        'summary_en': "A young apprentice dreams of eating sushi he cannot afford. A sympathetic customer treats him to it, but the encounter leaves an uncomfortable feeling. An emblematic short story of Shiga's style.",
        'summary_zh': "一位年轻学徒梦想着吃买不起的寿司。一位富有同情心的顾客请他吃了一顿，但这次相遇却留下了复杂的感受。志贺写作风格的代表短篇。",
    },
]


def main():
    print(f"=== Ingesting {len(BOOKS)} books ===\n")
    successes = []
    failures = []
    for i, book in enumerate(BOOKS, 1):
        print(f"--- [{i}/{len(BOOKS)}] {book['title_ja']} ({book['id']}) ---")
        try:
            process_one(book, WORK_DIR, REPO_ROOT)
            successes.append(book['id'])
        except Exception as e:
            print(f"  !!! FAILED: {type(e).__name__}: {e}")
            failures.append((book['id'], str(e)))
        print()

    print()
    print("=" * 60)
    print(f"Done. Success: {len(successes)}, Failed: {len(failures)}")
    if failures:
        print("\nFailed books:")
        for bid, err in failures:
            print(f"  {bid}: {err}")


if __name__ == "__main__":
    main()
