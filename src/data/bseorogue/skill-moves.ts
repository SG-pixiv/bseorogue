/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { MoveId } from "#enums/move-id";

/**
 * 실험체 스킬 [Q, W, E, R] 이 효과를 빌려 쓰는 포켓로그 기술 (ER 실험체 번호별)
 *
 * 이름 · 상성(역할군)은 블서로그 것으로 바뀌어요 (hooks.ts). 효과는 나중에 블서로그 것으로 바꿀 예정이에요.
 * 시작 6명은 직접 골랐고, 나머지는 역할군에 맞춰(물리 / 특수 · 위력) 자동으로 골라 둔 초안이에요. 직접 고쳐도 돼요.
 * 한 기술은 한 실험체만 써야 해요 (야생동물 · 보스 · 추가 스킬과도 겹치면 안 돼요. 테스트가 확인해요).
 */
export const SKILL_MOVES: Readonly<Record<number, readonly [MoveId, MoveId, MoveId, MoveId]>> = {
  1: [MoveId.POISON_FANG, MoveId.FORCE_PALM, MoveId.ZIPPY_ZAP, MoveId.BITTER_BLADE], // 재키
  2: [MoveId.MAGICAL_LEAF, MoveId.MYSTICAL_POWER, MoveId.QUIVER_DANCE, MoveId.MAGICAL_TORQUE], // 아야
  3: [MoveId.CHILLING_WATER, MoveId.INFERNAL_PARADE, MoveId.VACUUM_WAVE, MoveId.DRILL_RUN], // 피오라
  4: [MoveId.PAY_DAY, MoveId.ROCK_THROW, MoveId.HEART_STAMP, MoveId.BEHEMOTH_BASH], // 매그너스
  5: [MoveId.SHOCK_WAVE, MoveId.SUNSTEEL_STRIKE, MoveId.BLAZING_TORQUE, MoveId.PRECIPICE_BLADES], // 자히르
  6: [MoveId.BULLET_SEED, MoveId.METAL_CLAW, MoveId.MEDITATE, MoveId.STONE_EDGE], // 나딘
  7: [MoveId.POUNCE, MoveId.DEFEND_ORDER, MoveId.DOUBLE_HIT, MoveId.TRIPLE_ARROWS], // 현우
  8: [MoveId.VITAL_THROW, MoveId.SHARPEN, MoveId.LAST_RESPECTS, MoveId.HEAL_ORDER], // 하트
  9: [MoveId.COVET, MoveId.CRUSH_CLAW, MoveId.WATER_SHURIKEN, MoveId.LAST_RESORT], // 아이솔
  10: [MoveId.AERIAL_ACE, MoveId.FALSE_SURRENDER, MoveId.ROCK_TOMB, MoveId.DRAGON_RUSH], // 리 다이린
  11: [MoveId.SLASH, MoveId.DUAL_CHOP, MoveId.ACCELEROCK, MoveId.LEAF_BLADE], // 유키
  12: [MoveId.OVERDRIVE, MoveId.DRAGON_BREATH, MoveId.FIRE_BLAST, MoveId.DARK_PULSE], // 혜진
  13: [MoveId.BUBBLE, MoveId.SOFT_BOILED, MoveId.ZEN_HEADBUTT, MoveId.DRAGON_HAMMER], // 쇼우
  14: [MoveId.DRAINING_KISS, MoveId.SONIC_BOOM, MoveId.OBLIVION_WING, MoveId.AQUA_CUTTER], // 키아라
  15: [MoveId.SWIFT, MoveId.BOUNCY_BUBBLE, MoveId.TWISTER, MoveId.LIGHT_OF_RUIN], // 시셀라
  16: [MoveId.HIDDEN_POWER, MoveId.SPLISHY_SPLASH, MoveId.HYPERSPACE_HOLE, MoveId.ACID_ARMOR], // 실비아
  17: [MoveId.HYPER_VOICE, MoveId.SCARY_FACE, MoveId.ACID_SPRAY, MoveId.BLAST_BURN], // 아드리아나
  18: [MoveId.NIGHT_SLASH, MoveId.FLAME_WHEEL, MoveId.JET_PUNCH, MoveId.PSYCHO_CUT], // 쇼이치
  19: [MoveId.MUD_SHOT, MoveId.LANDS_WRATH, MoveId.GLACIATE, MoveId.SEED_FLARE], // 엠마
  20: [MoveId.FAIRY_WIND, MoveId.WILDBOLT_STORM, MoveId.ROCK_SLIDE, MoveId.HIGH_HORSEPOWER], // 레녹스
  21: [MoveId.AQUA_TAIL, MoveId.TRAILBLAZE, MoveId.TRIPLE_DIVE, MoveId.COMBAT_TORQUE], // 로지
  22: [MoveId.LIQUIDATION, MoveId.MEGA_PUNCH, MoveId.LOW_SWEEP, MoveId.VOLT_TACKLE], // 루크
  23: [MoveId.QUICK_ATTACK, MoveId.BUZZY_BUZZ, MoveId.SIZZLY_SLIDE, MoveId.BELCH], // 캐시
  24: [MoveId.SNORE, MoveId.FLOWER_TRICK, MoveId.SHADOW_SNEAK, MoveId.CHLOROBLAST], // 아델라
  25: [MoveId.LUNGE, MoveId.ICE_PUNCH, MoveId.AGILITY, MoveId.BLIZZARD], // 버니스
  26: [MoveId.BLOOD_MOON, MoveId.BADDY_BAD, MoveId.SACRED_FIRE, MoveId.LUSTER_PURGE], // 바바라
  27: [MoveId.BONE_RUSH, MoveId.SEED_BOMB, MoveId.POWER_UP_PUNCH, MoveId.DIRE_CLAW], // 알렉스
  28: [MoveId.STRUGGLE_BUG, MoveId.MUD_SLAP, MoveId.ACID, MoveId.BLEAKWIND_STORM], // 수아
  29: [MoveId.VISE_GRIP, MoveId.STUFF_CHEEKS, MoveId.ABSORB, MoveId.COLLISION_COURSE], // 레온
  30: [MoveId.CONSTRICT, MoveId.ROCK_CLIMB, MoveId.BODY_SLAM, MoveId.BITTER_MALICE], // 일레븐
  31: [MoveId.FLAME_CHARGE, MoveId.SPARK, MoveId.FIRST_IMPRESSION, MoveId.PLAY_ROUGH], // 리오
  32: [MoveId.FELL_STINGER, MoveId.ASTONISH, MoveId.ROCK_POLISH, MoveId.BOLT_STRIKE], // 윌리엄
  33: [MoveId.SALT_CURE, MoveId.TWIN_BEAM, MoveId.ELECTROWEB, MoveId.CRABHAMMER], // 니키
  34: [MoveId.ORIGIN_PULSE, MoveId.OCTAZOOKA, MoveId.MIGHTY_CLEAVE, MoveId.BARRIER], // 나타폰
  35: [MoveId.BREAKING_SWIPE, MoveId.NEEDLE_ARM, MoveId.HORN_LEECH, MoveId.AQUA_STEP], // 얀
  36: [MoveId.FLAME_BURST, MoveId.LUMINA_CRASH, MoveId.ICY_WIND, MoveId.SPARKLY_SWIRL], // 이바
  37: [MoveId.MAGNET_BOMB, MoveId.LICK, MoveId.FEINT, MoveId.SPIRIT_BREAK], // 다니엘
  38: [MoveId.TRUMP_CARD, MoveId.SNARL, MoveId.DRAGON_CLAW, MoveId.SIGNAL_BEAM], // 제니
  39: [MoveId.STOMP, MoveId.SACRED_SWORD, MoveId.SECRET_POWER, MoveId.PSYSHIELD_BASH], // 카밀로
  40: [MoveId.EGG_BOMB, MoveId.SCALE_SHOT, MoveId.AQUA_JET, MoveId.ROAR_OF_TIME], // 클로에
  41: [MoveId.POWDER_SNOW, MoveId.SWORDS_DANCE, MoveId.MYSTICAL_FIRE, MoveId.TORCH_SONG], // 요한
  42: [MoveId.DRAIN_PUNCH, MoveId.AMNESIA, MoveId.EMBER, MoveId.THUNDER], // 비앙카
  43: [MoveId.FREEZE_DRY, MoveId.TAIL_GLOW, MoveId.MATCHA_GOTCHA, MoveId.FRENZY_PLANT], // 셀린
  44: [MoveId.SHADOW_PUNCH, MoveId.COTTON_GUARD, MoveId.BULLET_PUNCH, MoveId.AURA_WHEEL], // 에키온
  45: [MoveId.GRASSY_GLIDE, MoveId.SMOG, MoveId.CONFUSION, MoveId.MILK_DRINK], // 마이
  46: [MoveId.VINE_WHIP, MoveId.REVENGE, MoveId.DUAL_WINGBEAT, MoveId.MOUNTAIN_GALE], // 에이든
  47: [MoveId.BUG_BITE, MoveId.INCINERATE, MoveId.BRICK_BREAK, MoveId.STRANGE_STEAM], // 라우라
  48: [MoveId.HEX, MoveId.WORK_UP, MoveId.WATER_GUN, MoveId.BLUE_FLARE], // 띠아
  49: [MoveId.STEAMROLLER, MoveId.THIEF, MoveId.ICE_SHARD, MoveId.MULTI_ATTACK], // 펠릭스
  50: [MoveId.DISARMING_VOICE, MoveId.SNIPE_SHOT, MoveId.STORED_POWER, MoveId.FIERY_WRATH], // 엘레나
  51: [MoveId.AIR_CUTTER, MoveId.DRAGON_RAGE, MoveId.ELECTRO_BALL, MoveId.JUDGMENT], // 프리야
  52: [MoveId.WRING_OUT, MoveId.STEAM_ERUPTION, MoveId.FIRE_FANG, MoveId.TAKE_HEART], // 아디나
  53: [MoveId.FALSE_SWIPE, MoveId.ZING_ZAP, MoveId.BONE_CLUB, MoveId.DRUM_BEATING], // 마커스
  54: [MoveId.HORN_ATTACK, MoveId.THUNDER_PUNCH, MoveId.MACH_PUNCH, MoveId.THUNDEROUS_KICK], // 칼라
  55: [MoveId.ACROBATICS, MoveId.LEECH_LIFE, MoveId.WATERFALL, MoveId.APPLE_ACID], // 에스텔
  56: [MoveId.FEINT_ATTACK, MoveId.FIRE_PUNCH, MoveId.CHIP_AWAY, MoveId.DOUBLE_EDGE], // 피올로
  57: [MoveId.PAYBACK, MoveId.ICE_FANG, MoveId.VICTORY_DANCE, MoveId.STEEL_ROLLER], // 마르티나
  58: [MoveId.RETALIATE, MoveId.SHADOW_CLAW, MoveId.FICKLE_BEAM, MoveId.AEROBLAST], // 헤이즈
  59: [MoveId.BRANCH_POKE, MoveId.STRENGTH, MoveId.ROCK_SMASH, MoveId.FLOATY_FALL], // 아이작
  60: [MoveId.GUST, MoveId.SPACIAL_REND, MoveId.GRAV_APPLE, MoveId.PSYSTRIKE], // 타지아
  61: [MoveId.VENOSHOCK, MoveId.WATER_PULSE, MoveId.TIDY_UP, MoveId.ERUPTION], // 이렘
  62: [MoveId.POISON_JAB, MoveId.FISHIOUS_REND, MoveId.FREEZING_GLARE, MoveId.BRAVE_BIRD], // 테오도르
  63: [MoveId.ASSURANCE, MoveId.RAPID_SPIN, MoveId.THUNDER_FANG, MoveId.DYNAMIC_PUNCH], // 이안
  64: [MoveId.PLUCK, MoveId.SMACK_DOWN, MoveId.NIGHT_DAZE, MoveId.WICKED_TORQUE], // 바냐
  65: [MoveId.AVALANCHE, MoveId.KOWTOW_CLEAVE, MoveId.FAKE_OUT, MoveId.WAVE_CRASH], // 데비&마를렌
  66: [MoveId.CLEAR_SMOG, MoveId.SPRINGTIDE_STORM, MoveId.SUBMISSION, MoveId.MALIGNANT_CHAIN], // 아르다
  67: [MoveId.HOLD_BACK, MoveId.ROCK_BLAST, MoveId.BOLT_BEAK, MoveId.GLACIAL_LANCE], // 아비게일
  68: [MoveId.BONEMERANG, MoveId.NATURES_MADNESS, MoveId.ICICLE_SPEAR, MoveId.IRON_TAIL], // 알론소
  69: [MoveId.TACHYON_CUTTER, MoveId.THUNDER_SHOCK, MoveId.NIGHT_SHADE, MoveId.REVELATION_DANCE], // 레니
  70: [MoveId.POWER_WHIP, MoveId.SHIFT_GEAR, MoveId.DOUBLE_TEAM, MoveId.HYPER_DRILL], // 츠바메
  71: [MoveId.PIN_MISSILE, MoveId.HARDEN, MoveId.STOMPING_TANTRUM, MoveId.BLAZE_KICK], // 케네스
  72: [MoveId.POUND, MoveId.COIL, MoveId.X_SCISSOR, MoveId.GIGATON_HAMMER], // 카티야
  73: [MoveId.ECHOED_VOICE, MoveId.LUNAR_BLESSING, MoveId.IRON_DEFENSE, MoveId.FIERY_DANCE], // 샬럿
  74: [MoveId.GEAR_GRIND, MoveId.SHELTER, MoveId.STORM_THROW, MoveId.FIRE_LASH], // 다르코
  75: [MoveId.PSYCHIC_NOISE, MoveId.TECHNO_BLAST, MoveId.AURORA_BEAM, MoveId.FREEZY_FROST], // 르노어
  76: [MoveId.KARATE_CHOP, MoveId.PIKA_PAPOW, MoveId.DOUBLE_IRON_BASH, MoveId.ESPER_WING], // 가넷
  77: [MoveId.BURNING_JEALOUSY, MoveId.MUDDY_WATER, MoveId.TAIL_SLAP, MoveId.MIST_BALL], // 유민
  78: [MoveId.LEAFAGE, MoveId.MEGA_DRAIN, MoveId.DRILL_PECK, MoveId.MEGAHORN], // 히스이
  79: [MoveId.PSYBEAM, MoveId.LASH_OUT, MoveId.EERIE_SPELL, MoveId.OVERHEAT], // 유스티나
  80: [MoveId.CUT, MoveId.FURY_CUTTER, MoveId.SKY_UPPERCUT, MoveId.MEGA_KICK], // 이슈트반
  81: [MoveId.DARKEST_LARIAT, MoveId.ICE_SPINNER, MoveId.GLITZY_GLOW, MoveId.WATER_SPOUT], // 니아
  82: [MoveId.DOUBLE_KICK, MoveId.TROP_KICK, MoveId.ANCHOR_SHOT, MoveId.PLASMA_FISTS], // 슈린
  83: [MoveId.JAW_LOCK, MoveId.NUZZLE, MoveId.SECRET_SWORD, MoveId.HIGH_JUMP_KICK], // 헨리
  84: [MoveId.SCRATCH, MoveId.RAZOR_SHELL, MoveId.SKITTER_SMACK, MoveId.GLAIVE_RUSH], // 블레어
  85: [MoveId.RUINATION, MoveId.WITHDRAW, MoveId.ICICLE_CRASH, MoveId.INFERNO], // 미르카
  86: [MoveId.RAGE_FIST, MoveId.ROLLING_KICK, MoveId.CEASELESS_EDGE, MoveId.PSYCHIC_FANGS], // 펜리르
  87: [MoveId.CHATTER, MoveId.NASTY_PLOT, MoveId.SHADOW_BONE, MoveId.ELECTRO_DRIFT], // 코렐라인
  88: [MoveId.STONE_AXE, MoveId.STEEL_WING, MoveId.DIZZY_PUNCH, MoveId.DIAMOND_STORM], // 비형
  89: [MoveId.PSYBLADE, MoveId.BARB_BARRAGE, MoveId.POPULATION_BOMB, MoveId.NIHIL_LIGHT], // 크레이버
  90: [MoveId.SLUDGE, MoveId.TEMPER_FLARE, MoveId.SHELL_SMASH, MoveId.PETAL_DANCE], // 루치아
  91: [MoveId.PSYWAVE, MoveId.POWER_TRIP, MoveId.JUNGLE_HEALING, MoveId.CHARGE], // 세레스
};
