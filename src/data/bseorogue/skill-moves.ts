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
  1: [MoveId.STOMP, MoveId.TOXIC, MoveId.DIZZY_PUNCH, MoveId.FLARE_BLITZ], // 재키
  2: [MoveId.ICY_WIND, MoveId.COSMIC_POWER, MoveId.DISCHARGE, MoveId.SEARING_SHOT], // 아야
  3: [MoveId.ROCK_SMASH, MoveId.FEATHER_DANCE, MoveId.X_SCISSOR, MoveId.SUNSTEEL_STRIKE], // 피오라
  4: [MoveId.POISON_TAIL, MoveId.GROWTH, MoveId.WILD_CHARGE, MoveId.HEADLONG_RUSH], // 매그너스
  5: [MoveId.STRUGGLE_BUG, MoveId.SPICY_EXTRACT, MoveId.SCORCHING_SANDS, MoveId.FIRE_BLAST], // 자히르
  6: [MoveId.BULLET_SEED, MoveId.FOCUS_ENERGY, MoveId.THOUSAND_ARROWS, MoveId.STONE_EDGE], // 나딘
  7: [MoveId.LEAFAGE, MoveId.FLASH, MoveId.BOLT_BEAK, MoveId.FOUL_PLAY], // 현우
  8: [MoveId.LAST_RESPECTS, MoveId.DOUBLE_TEAM, MoveId.THUNDEROUS_KICK, MoveId.HIGH_HORSEPOWER], // 하트
  9: [MoveId.PAY_DAY, MoveId.EERIE_IMPULSE, MoveId.AQUA_STEP, MoveId.AXE_KICK], // 아이솔
  10: [MoveId.THIEF, MoveId.SHELL_SMASH, MoveId.FIRE_PUNCH, MoveId.MIGHTY_CLEAVE], // 리 다이린
  11: [MoveId.SLASH, MoveId.SWORDS_DANCE, MoveId.SACRED_SWORD, MoveId.LEAF_BLADE], // 유키
  12: [MoveId.SHADOW_BALL, MoveId.HEX, MoveId.CONFUSE_RAY, MoveId.DARK_PULSE], // 혜진
  13: [MoveId.ICE_FANG, MoveId.NOBLE_ROAR, MoveId.ZEN_HEADBUTT, MoveId.BEHEMOTH_BASH], // 쇼우
  14: [MoveId.BULLDOZE, MoveId.TAKE_HEART, MoveId.PETAL_BLIZZARD, MoveId.COMBAT_TORQUE], // 키아라
  15: [MoveId.BUBBLE_BEAM, MoveId.SMOKESCREEN, MoveId.BUG_BUZZ, MoveId.DRACO_METEOR], // 시셀라
  16: [MoveId.HIDDEN_POWER, MoveId.QUIVER_DANCE, MoveId.SECRET_SWORD, MoveId.ORIGIN_PULSE], // 실비아
  17: [MoveId.BRINE, MoveId.CONFIDE, MoveId.APPLE_ACID, MoveId.MAKE_IT_RAIN], // 아드리아나
  18: [MoveId.NIGHT_SLASH, MoveId.QUICK_ATTACK, MoveId.SUCKER_PUNCH, MoveId.PSYCHO_CUT], // 쇼이치
  19: [MoveId.DRAINING_KISS, MoveId.SCARY_FACE, MoveId.ALLURING_VOICE, MoveId.BLUE_FLARE], // 엠마
  20: [MoveId.COVET, MoveId.HARDEN, MoveId.ROCK_SLIDE, MoveId.POWER_WHIP], // 레녹스
  21: [MoveId.STORM_THROW, MoveId.SUPERSONIC, MoveId.WAKE_UP_SLAP, MoveId.PYRO_BALL], // 로지
  22: [MoveId.SIZZLY_SLIDE, MoveId.MEDITATE, MoveId.DRILL_RUN, MoveId.SUPERCELL_SLAM], // 루크
  23: [MoveId.RAGE_FIST, MoveId.DEFOG, MoveId.LUNGE, MoveId.FUSION_BOLT], // 캐시
  24: [MoveId.CLEAR_SMOG, MoveId.AGILITY, MoveId.ESPER_WING, MoveId.WILDBOLT_STORM], // 아델라
  25: [MoveId.PURSUIT, MoveId.CHARM, MoveId.DIRE_CLAW, MoveId.EARTHQUAKE], // 버니스
  26: [MoveId.EMBER, MoveId.DEFENSE_CURL, MoveId.POWER_GEM, MoveId.STEAM_ERUPTION], // 바바라
  27: [MoveId.SMACK_DOWN, MoveId.SCREECH, MoveId.STRENGTH, MoveId.SPIN_OUT], // 알렉스
  28: [MoveId.BREAKING_SWIPE, MoveId.CHARGE, MoveId.DRAGON_CLAW, MoveId.WOOD_HAMMER], // 수아
  29: [MoveId.VISE_GRIP, MoveId.STUN_SPORE, MoveId.RAZOR_SHELL, MoveId.COLLISION_COURSE], // 레온
  30: [MoveId.HAMMER_ARM, MoveId.IRON_DEFENSE, MoveId.BODY_SLAM, MoveId.GIGA_IMPACT], // 일레븐
  31: [MoveId.ROCK_TOMB, MoveId.SING, MoveId.DRUM_BEATING, MoveId.GLACIAL_LANCE], // 리오
  32: [MoveId.LOW_SWEEP, MoveId.NASTY_PLOT, MoveId.FLOWER_TRICK, MoveId.BOLT_STRIKE], // 윌리엄
  33: [MoveId.SALT_CURE, MoveId.POISON_POWDER, MoveId.WATERFALL, MoveId.CRABHAMMER], // 니키
  34: [MoveId.MUD_SHOT, MoveId.MINIMIZE, MoveId.SHELL_SIDE_ARM, MoveId.SANDSEAR_STORM], // 나타폰
  35: [MoveId.RAPID_SPIN, MoveId.HYPNOSIS, MoveId.HORN_LEECH, MoveId.CROSS_CHOP], // 얀
  36: [MoveId.BOUNCY_BUBBLE, MoveId.COTTON_GUARD, MoveId.SIGNAL_BEAM, MoveId.SPARKLY_SWIRL], // 이바
  37: [MoveId.FELL_STINGER, MoveId.SWEET_KISS, MoveId.SPIRIT_BREAK, MoveId.PRECIPICE_BLADES], // 다니엘
  38: [MoveId.SCRATCH, MoveId.WORK_UP, MoveId.AQUA_CUTTER, MoveId.DIAMOND_STORM], // 제니
  39: [MoveId.ICE_BALL, MoveId.TICKLE, MoveId.SECRET_POWER, MoveId.HYPERSPACE_FURY], // 카밀로
  40: [MoveId.FLAME_CHARGE, MoveId.WITHDRAW, MoveId.ICICLE_CRASH, MoveId.AURA_WHEEL], // 클로에
  41: [MoveId.DISARMING_VOICE, MoveId.THUNDER_WAVE, MoveId.AIR_SLASH, MoveId.TECHNO_BLAST], // 요한
  42: [MoveId.CONFUSION, MoveId.COIL, MoveId.SPLISHY_SPLASH, MoveId.LEAF_STORM], // 비앙카
  43: [MoveId.CHARGE_BEAM, MoveId.PLAY_NICE, MoveId.MATCHA_GOTCHA, MoveId.HEAT_WAVE], // 셀린
  44: [MoveId.PAYBACK, MoveId.SHIFT_GEAR, MoveId.DRILL_PECK, MoveId.MEGAHORN], // 에키온
  45: [MoveId.GRASSY_GLIDE, MoveId.FAKE_TEARS, MoveId.CROSS_POISON, MoveId.GLAIVE_RUSH], // 마이
  46: [MoveId.ROLLOUT, MoveId.SHARPEN, MoveId.SHADOW_BONE, MoveId.DRAGON_HAMMER], // 에이든
  47: [MoveId.BUG_BITE, MoveId.METAL_SOUND, MoveId.KOWTOW_CLEAVE, MoveId.SAPPY_SEED], // 라우라
  48: [MoveId.ROUND, MoveId.AUTOTOMIZE, MoveId.SLUDGE_BOMB, MoveId.SEED_FLARE], // 띠아
  49: [MoveId.FALSE_SWIPE, MoveId.TAR_SHOT, MoveId.SHADOW_CLAW, MoveId.DRAGON_ASCENT], // 펠릭스
  50: [MoveId.STEAMROLLER, MoveId.TIDY_UP, MoveId.SPECTRAL_THIEF, MoveId.VOLT_TACKLE], // 엘레나
  51: [MoveId.AIR_CUTTER, MoveId.FLATTER, MoveId.HYDRO_STEAM, MoveId.HYDRO_PUMP], // 프리야
  52: [MoveId.FAIRY_WIND, MoveId.ROCK_POLISH, MoveId.FIERY_DANCE, MoveId.SPACIAL_REND], // 아디나
  53: [MoveId.THUNDER_FANG, MoveId.WILL_O_WISP, MoveId.AQUA_TAIL, MoveId.NOXIOUS_TORQUE], // 마커스
  54: [MoveId.HORN_ATTACK, MoveId.BARRIER, MoveId.LIQUIDATION, MoveId.MAGICAL_TORQUE], // 칼라
  55: [MoveId.ACROBATICS, MoveId.SLEEP_POWDER, MoveId.WICKED_TORQUE, MoveId.HYPER_DRILL], // 에스텔
  56: [MoveId.FEINT_ATTACK, MoveId.TAIL_GLOW, MoveId.CHIP_AWAY, MoveId.DOUBLE_EDGE], // 피올로
  57: [MoveId.BARB_BARRAGE, MoveId.LOVELY_KISS, MoveId.SKITTER_SMACK, MoveId.SACRED_FIRE], // 마르티나
  58: [MoveId.POWDER_SNOW, MoveId.ACID_ARMOR, MoveId.FICKLE_BEAM, MoveId.FUSION_FLARE], // 헤이즈
  59: [MoveId.POWER_UP_PUNCH, MoveId.SPORE, MoveId.ATTACK_ORDER, MoveId.IVY_CUDGEL], // 아이작
  60: [MoveId.GUST, MoveId.AMNESIA, MoveId.BURNING_JEALOUSY, MoveId.PSYSTRIKE], // 타지아
  61: [MoveId.VENOSHOCK, MoveId.GRASS_WHISTLE, MoveId.SCALD, MoveId.MIST_BALL], // 이렘
  62: [MoveId.TRAILBLAZE, MoveId.SHELTER, MoveId.SMELLING_SALTS, MoveId.MOUNTAIN_GALE], // 테오도르
  63: [MoveId.HEART_STAMP, MoveId.KINESIS, MoveId.ZING_ZAP, MoveId.HEAD_CHARGE], // 이안
  64: [MoveId.PLUCK, MoveId.DEFEND_ORDER, MoveId.FACADE, MoveId.ICE_HAMMER], // 바냐
  65: [MoveId.ASTONISH, MoveId.SAND_ATTACK, MoveId.FISHIOUS_REND, MoveId.WAVE_CRASH], // 데비&마를렌
  66: [MoveId.ACID, MoveId.VICTORY_DANCE, MoveId.LUMINA_CRASH, MoveId.MALIGNANT_CHAIN], // 아르다
  67: [MoveId.HOLD_BACK, MoveId.SWAGGER, MoveId.LANDS_WRATH, MoveId.BRAVE_BIRD], // 아비게일
  68: [MoveId.SNAP_TRAP, MoveId.PARTING_SHOT, MoveId.ICE_PUNCH, MoveId.THROAT_CHOP], // 알론소
  69: [MoveId.FLASH_CANNON, MoveId.HEAL_PULSE, MoveId.PROTECT, MoveId.MOONBLAST], // 레니
  70: [MoveId.FLAME_WHEEL, MoveId.TEARFUL_LOOK, MoveId.RETALIATE, MoveId.ICE_SPINNER], // 츠바메
  71: [MoveId.AERIAL_ACE, MoveId.DECORATE, MoveId.STOMPING_TANTRUM, MoveId.BLAZE_KICK], // 케네스
  72: [MoveId.POUND, MoveId.GLARE, MoveId.THUNDER_PUNCH, MoveId.LASH_OUT], // 카티야
  73: [MoveId.SYRUP_BOMB, MoveId.TOXIC_THREAD, MoveId.SURF, MoveId.LUSTER_PURGE], // 샬럿
  74: [MoveId.MORTAL_SPIN, MoveId.DRAIN_PUNCH, MoveId.TRIPLE_ARROWS, MoveId.JAW_LOCK], // 다르코
  75: [MoveId.INFERNAL_PARADE, MoveId.SILVER_WIND, MoveId.HYPER_VOICE, MoveId.FREEZY_FROST], // 르노어
  76: [MoveId.KARATE_CHOP, MoveId.FIRE_FANG, MoveId.CRUSH_CLAW, MoveId.POISON_JAB], // 가넷
  77: [MoveId.ACID_SPRAY, MoveId.PSYCHIC_NOISE, MoveId.TORCH_SONG, MoveId.PHOTON_GEYSER], // 유민
  78: [MoveId.RAZOR_LEAF, MoveId.STEEL_WING, MoveId.DARKEST_LARIAT, MoveId.RAGING_BULL], // 히스이
  79: [MoveId.LEAF_TORNADO, MoveId.OBLIVION_WING, MoveId.EXTRASENSORY, MoveId.OVERHEAT], // 유스티나
  80: [MoveId.CUT, MoveId.ASSURANCE, MoveId.SKY_UPPERCUT, MoveId.TEMPER_FLARE], // 이슈트반
  81: [MoveId.WATER_GUN, MoveId.WATER_PULSE, MoveId.OVERDRIVE, MoveId.SPRINGTIDE_STORM], // 니아
  82: [MoveId.VINE_WHIP, MoveId.BRICK_BREAK, MoveId.ANCHOR_SHOT, MoveId.LEECH_LIFE], // 슈린
  83: [MoveId.BUBBLE, MoveId.AURORA_BEAM, MoveId.LAVA_PLUME, MoveId.SLUDGE_WAVE], // 헨리
  84: [MoveId.FURY_CUTTER, MoveId.MAGNET_BOMB, MoveId.FIRE_LASH, MoveId.SEED_BOMB], // 블레어
  85: [MoveId.LICK, MoveId.NEEDLE_ARM, MoveId.THOUSAND_WAVES, MoveId.PSYSHIELD_BASH], // 미르카
  86: [MoveId.POUNCE, MoveId.FORCE_PALM, MoveId.BLAZING_TORQUE, MoveId.PSYCHIC_FANGS], // 펜리르
  87: [MoveId.CHATTER, MoveId.FROST_BREATH, MoveId.EXPANDING_FORCE, MoveId.ELECTRO_DRIFT], // 코렐라인
  88: [MoveId.ROCK_THROW, MoveId.ORDER_UP, MoveId.PSYBLADE, MoveId.TROP_KICK], // 비형
  89: [MoveId.ELECTROWEB, MoveId.SWIFT, MoveId.STRANGE_STEAM, MoveId.NIHIL_LIGHT], // 크레이버
  90: [MoveId.SLUDGE, MoveId.PSYBEAM, MoveId.HYPERSPACE_HOLE, MoveId.AEROBLAST], // 루치아
  91: [MoveId.METAL_CLAW, MoveId.SHADOW_PUNCH, MoveId.GRAV_APPLE, MoveId.FALSE_SURRENDER], // 세레스
};
