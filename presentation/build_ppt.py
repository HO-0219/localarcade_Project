from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "Game"
OUT = ROOT / "presentation" / "Local_Arcade_Portfolio.pptx"

# Editorial portfolio palette. Most slides use paper-like backgrounds and
# restrained blue accents so screenshots and engineering explanations lead.
BG = RGBColor(246, 247, 249)
PANEL = RGBColor(255, 255, 255)
PANEL2 = RGBColor(238, 241, 245)
WHITE = RGBColor(31, 41, 55)
MUTED = RGBColor(91, 103, 120)
MINT = RGBColor(39, 111, 151)
PINK = RGBColor(73, 103, 145)
YELLOW = RGBColor(142, 105, 54)
BLUE = RGBColor(49, 94, 154)
LINE = RGBColor(210, 216, 224)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

def rect(slide, x, y, w, h, fill=PANEL, line=None, radius=False):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                                   Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid(); shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = line or fill
    return shape

def text(slide, value, x, y, w, h, size=18, color=WHITE, bold=False,
         font="Malgun Gothic", align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.clear(); tf.word_wrap = True; tf.vertical_anchor = valign
    p = tf.paragraphs[0]; p.text = value; p.alignment = align
    p.font.name = font; p.font.size = Pt(size); p.font.bold = bold; p.font.color.rgb = color
    return box

def rich_lines(slide, lines, x, y, w, h, size=16, gap=8):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.clear(); tf.word_wrap = True
    for i, (lead, body, color) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap); p.font.name = "Malgun Gothic"; p.font.size = Pt(size); p.font.color.rgb = WHITE
        r = p.add_run(); r.text = lead; r.font.bold = True; r.font.color.rgb = color
        r = p.add_run(); r.text = body; r.font.color.rgb = WHITE
    return box

def base(title, kicker, number):
    s = prs.slides.add_slide(blank); s.background.fill.solid(); s.background.fill.fore_color.rgb = BG
    text(s, kicker, .62, .30, 6, .25, 9, MUTED, False, "Arial")
    text(s, title, .62, .62, 11.9, .55, 25, WHITE, True)
    rect(s, .55, 1.19, 12.2, .015, LINE, LINE, False)
    text(s, f"Local Arcade  |  {number:02d}", 10.65, 7.12, 2.1, .2, 8, MUTED, False, "Arial", PP_ALIGN.RIGHT)
    return s

def add_image(slide, path, x, y, w, h, crop_top=0, mode="contain"):
    path = Path(path)
    with Image.open(path) as im:
        iw, ih = im.size
    effective_h = ih * (1-crop_top) if crop_top else ih
    target_ratio = w/h; image_ratio = iw/effective_h
    if mode == "contain":
        # Preserve the full screenshot. Empty space is intentional and makes UI
        # context easier to understand than aggressive cropping.
        rect(slide, x, y, w, h, PANEL2, LINE, False)
        if image_ratio > target_ratio:
            ph = w / image_ratio
            px, py, pw = x, y + (h-ph)/2, w
        else:
            pw = h * image_ratio
            px, py, ph = x + (w-pw)/2, y, h
        pic = slide.shapes.add_picture(str(path), Inches(px), Inches(py), width=Inches(pw), height=Inches(ph))
    else:
        pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))
        if crop_top: pic.crop_top = crop_top
        if image_ratio > target_ratio:
            extra = 1 - target_ratio/image_ratio; pic.crop_left = extra/2; pic.crop_right = extra/2
        elif image_ratio < target_ratio:
            extra = 1 - image_ratio/target_ratio; pic.crop_top = max(pic.crop_top, extra/2); pic.crop_bottom = extra/2
    pic.line.color.rgb = LINE
    return pic

def code(slide, value, x, y, w, h, title="IMPLEMENTATION"):
    rect(slide, x, y, w, h, RGBColor(32, 39, 50), RGBColor(32, 39, 50))
    text(slide, title.title(), x+.22, y+.15, w-.44, .2, 9, RGBColor(168, 190, 220), False, "Arial")
    text(slide, value, x+.22, y+.45, w-.44, h-.58, 11.3, RGBColor(232, 236, 242), False, "Consolas")

def pill(slide, label, x, y, w, color=MINT):
    rect(slide, x, y, w, .38, PANEL2, color)
    text(slide, label, x, y+.08, w, .18, 10, color, True, "Arial", PP_ALIGN.CENTER)

# 1. Cover
s = prs.slides.add_slide(blank); s.background.fill.solid(); s.background.fill.fore_color.rgb = BG
add_image(s, GAME / "메인화면.png", 0, 0, 13.333, 7.5, .04, "fill")
overlay = rect(s, 0, 0, 13.333, 7.5, RGBColor(244,247,250), RGBColor(244,247,250), False); overlay.fill.transparency = 18
rect(s, .7, 1.0, .05, 4.6, BLUE, BLUE, False)
text(s, "LOCAL", 1.05, 1.05, 6.8, .72, 43, WHITE, True, "Arial")
text(s, "ARCADE", 1.05, 1.72, 6.8, .78, 48, MINT, True, "Arial")
text(s, "LAN 기반 실시간 멀티플레이 게임 플랫폼", 1.08, 2.72, 7.2, .4, 20, WHITE, True)
text(s, "게임 · 채팅 · AI 학습 퀴즈를 하나의 로컬 서비스로", 1.08, 3.25, 7.4, .34, 15, RGBColor(55, 65, 81), True)
text(s, "개인 프로젝트 · Full Stack · Backend 중심 설계", 1.08, 4.28, 6.8, .3, 13, WHITE, True)
text(s, "React + TypeScript  /  Spring Boot + MySQL  /  OpenAI Responses API", 1.08, 4.82, 7.7, .3, 11, MUTED, False, "Arial")
text(s, "2026  ·  기획 / 설계 / 구현 / 테스트", 1.08, 5.32, 5.5, .25, 10, MUTED, False, "Arial")

# 2. Agenda
s = base("Contents", "PORTFOLIO STRUCTURE", 2)
sections = [
    ("01", "Project", "문제 정의 · 사용자 흐름 · 구현 범위", MINT),
    ("02", "Architecture", "기술 선택 · 서버 중심 상태 · 데이터 구조", BLUE),
    ("03", "Engineering", "반복 트래픽 · 동시 명령 · 트랜잭션 · 통신", YELLOW),
    ("04", "Features", "게임 규칙 · AI 퀴즈 · 운영 기능", PINK),
    ("05", "Validation", "테스트 · 한계 · 확장 전략 · 회고", MINT),
]
for i, (n, head, body, c) in enumerate(sections):
    y = 1.48 + i * 1.02
    text(s, n, .75, y + .18, .55, .28, 13, c, True, "Arial")
    text(s, head, 1.55, y + .12, 2.05, .32, 17, WHITE, True, "Arial")
    text(s, body, 3.85, y + .15, 7.85, .32, 14, MUTED)
    rect(s, .75, y + .76, 11.55, .012, LINE, LINE, False)
text(s, "핵심 관점", .75, 6.65, 1.4, .25, 11, MINT, True)
text(s, "여러 사용자의 요청이 동시에 들어와도 공유 상태와 크레딧을 설명 가능하게 유지하는 방법", 2.15, 6.6, 10.0, .35, 15, WHITE, True)

# 3. Overview
s = base("프로젝트 소개", "01 · OVERVIEW", 3)
add_image(s, GAME / "참여코드 입력 화면.png", .65, 1.48, 5.7, 2.65)
add_image(s, GAME / "게임 종류 및 메뉴 창.png", .65, 4.38, 5.7, 1.42)
rect(s, 6.7, 1.48, 5.95, 4.95, PANEL, LINE)
text(s, "참여 코드 하나로 시작하는 로컬 아케이드", 7.05, 1.8, 5.2, .55, 22, WHITE, True)
rich_lines(s, [("형태  ", "개인 프로젝트 · 기여도 100%", MINT),("대상  ", "동일 LAN 내 최대 6명", PINK),("접속  ", "6자리 코드 + 닉네임", YELLOW),("콘텐츠  ", "야추 · 레이싱 · 행맨 · 마피아 · AI 퀴즈", BLUE),("운영  ", "공용 채팅 · 크레딧 · 랭킹 · 관리자 페이지", MINT)], 7.05, 2.65, 5.05, 2.75, 16)
text(s, "목표: 화면 구현을 넘어 여러 사용자가 공유하는 상태를 서버 중심으로 일관되게 관리", 7.05, 5.55, 5.0, .58, 14, WHITE, True)

# 4. Stack — explain responsibility and selection instead of listing logos.
s = base("기술 구성과 역할", "02 · Technology", 4)
stack_rows = [
    ("Client", "React 18 · TypeScript · Vite", "사용자 입력, 게임 화면과 애니메이션. 서버 상태를 표현하는 역할로 제한", MINT),
    ("Server", "Java 21 · Spring Boot 3.4", "게임 규칙 검증, 공유 상태 변경, 명령 순서와 세션 관리", BLUE),
    ("Data", "MySQL 8 · Spring Data JPA", "플레이어 크레딧과 검증된 퀴즈를 영속화하고 트랜잭션 경계 제공", YELLOW),
    ("AI", "OpenAI Responses API · JSON Schema", "로컬 위키 기반 문제 생성 후 형식·정답·출처를 서버에서 재검증", PINK),
    ("Network", "HTTP REST · Bearer Token · LAN", "1초 폴링으로 상태 동기화. 현재 규모에서 단순성과 복구 용이성 선택", MINT),
]
for i, (area, tech, reason, c) in enumerate(stack_rows):
    y = 1.48 + i * 1.03
    text(s, area, .75, y + .16, 1.2, .28, 13, c, True, "Arial")
    text(s, tech, 2.05, y + .12, 3.35, .32, 15, WHITE, True)
    text(s, reason, 5.65, y + .10, 6.45, .48, 12.5, MUTED)
    rect(s, .75, y + .76, 11.5, .012, LINE, LINE, False)

# 4. Architecture
s = base("System Architecture", "03 · DESIGN", 4)
text(s, "브라우저 1~6명", .65, 1.55, 2.2, .35, 16, WHITE, True)
for i in range(3):
    rect(s,.7+i*.72,2.0,.55,.72,PANEL2,MINT); text(s,"USER",.7+i*.72,2.25,.55,.15,7,MINT,True,"Arial",PP_ALIGN.CENTER)
text(s,"HTTP · 1초 폴링",3.0,2.17,1.55,.25,11,MUTED,True,"Arial",PP_ALIGN.CENTER)
text(s,"→",4.35,2.02,.5,.5,27,MINT,True,"Arial",PP_ALIGN.CENTER)
rect(s,4.9,1.63,2.2,1.35,PANEL,MINT); text(s,"React + TypeScript",5.05,1.98,1.9,.3,15,WHITE,True,"Arial",PP_ALIGN.CENTER)
text(s,"REST API · Token",7.2,2.17,1.55,.25,11,MUTED,True,"Arial",PP_ALIGN.CENTER); text(s,"→",8.55,2.02,.5,.5,27,PINK,True,"Arial",PP_ALIGN.CENTER)
rect(s,9.05,1.63,3.05,1.35,PANEL,PINK); text(s,"Spring Boot Server",9.25,1.98,2.65,.3,16,WHITE,True,"Arial",PP_ALIGN.CENTER)
services=[("GAME STATE","턴 · 결과 · 크레딧",MINT),("COMMAND QUEUE","요청 순차 처리",PINK),("QUIZ PIPELINE","생성 · 검증 · 저장",YELLOW)]
for i,(a,b,c) in enumerate(services):
    x=.8+i*4.15; rect(s,x,3.65,3.7,1.1,PANEL,LINE); text(s,a,x+.2,3.91,3.3,.22,12,c,True,"Arial",PP_ALIGN.CENTER); text(s,b,x+.2,4.3,3.3,.2,12,WHITE,False,"Arial",PP_ALIGN.CENTER)
text(s,"↓",3.0,5.0,.4,.4,25,MINT,True,"Arial",PP_ALIGN.CENTER); text(s,"↓",9.9,5.0,.4,.4,25,YELLOW,True,"Arial",PP_ALIGN.CENTER)
rect(s,1.15,5.55,4.2,.75,PANEL2,BLUE); text(s,"MySQL · 플레이어 / 문제 / 크레딧",1.35,5.79,3.8,.25,13,WHITE,True,"Arial",PP_ALIGN.CENTER)
rect(s,7.6,5.55,4.2,.75,PANEL2,YELLOW); text(s,"LLM Wiki → OpenAI Responses API",7.8,5.79,3.8,.25,13,WHITE,True,"Arial",PP_ALIGN.CENTER)
text(s,"최종 판정은 서버가 담당하고 클라이언트는 입력과 표현을 담당",3.2,6.65,6.9,.28,13,MUTED,True,"Arial",PP_ALIGN.CENTER)

# 5. User flow
s = base("User Flow", "04 · EXPERIENCE", 5)
steps=[("01","서버 실행","참여 코드 발급"),("02","빠른 입장","코드 + 닉네임"),("03","로비","게임 선택"),("04","멀티플레이","참가 · 턴 · 채팅"),("05","결과 정산","크레딧 · 랭킹")]
for i,(n,a,b) in enumerate(steps):
    x=.6+i*2.52; rect(s,x,1.65,2.2,1.25,PANEL, [MINT,PINK,YELLOW,BLUE,MINT][i]); text(s,n,x+.15,1.82,.45,.25,12,[MINT,PINK,YELLOW,BLUE,MINT][i],True,"Arial"); text(s,a,x+.15,2.15,1.9,.25,15,WHITE,True); text(s,b,x+.15,2.51,1.9,.2,11,MUTED)
    if i<4: text(s,"→",x+2.2,2.0,.32,.4,20,MUTED,True,"Arial",PP_ALIGN.CENTER)
add_image(s, GAME / "메인화면.png", .65, 3.35, 7.3, 3.25)
add_image(s, GAME / "관리자 페이지 플레이어 점수 관리 및 AI문제 출제 활성화 버튼.png", 8.25, 3.35, 4.4, 3.25)

# 6. Yacht
s=base("턴과 상태를 서버가 관리하는 멀티플레이 야추", "05 · CORE GAME", 6)
add_image(s,GAME/"야추게임화면.png",.65,1.45,5.25,5.45)
rich_lines(s,[("READY  ","2명 이상, 동일 참가 점수 검증",MINT),("ROLL  ","턴당 최대 3회 · HOLD 유지",PINK),("SCORE  ","12개 항목과 상단 보너스 계산",YELLOW),("RESULT  ","공동 우승 · 기권 · 환불 · 재경기",BLUE)],6.25,1.62,5.8,2.1,15)
code(s,"YachtGame g = activeTurn(player);\n\nif (!visibleDice.equals(serverDice))\n    throw new IllegalArgumentException(...);\n\nif (sheet.containsKey(category))\n    throw new IllegalArgumentException(...);\n\nint points = calculate(category, g.dice);\nsheet.put(category, points);",6.25,3.85,6.0,2.78,"SERVER-SIDE VALIDATION")

# 7. Racing
s=base("모든 플레이어가 같은 결과를 공유하는 레이싱", "06 · SYNCHRONIZATION", 7)
add_image(s,GAME/"달팽이 레이싱 .png",.65,1.5,5.8,5.35)
add_image(s,GAME/"달팽이 레이싱 종료 화면.png",6.7,1.5,2.8,2.45)
code(s,"List<Integer> order = shuffle(1, 2, 3, 4, 5);\nlong raceId = System.currentTimeMillis();\n\n// 서버가 단일 결과를 생성\nlastResult = new RaceResult(raceId, order);\n\n// 브라우저는 전달받은 순위만 표현\nsetRaceOrder(out.state.race.lastResult.order);",9.75,1.5,2.9,2.45,"ONE SOURCE OF TRUTH")
rich_lines(s,[("① 판정  ","랜덤 순위와 보상은 서버에서 한 번만",MINT),("② 식별  ","raceId로 새 경기와 중복 실행 구분",PINK),("③ 표현  ","카운트다운·주행·시상대는 클라이언트",YELLOW)],6.7,4.35,5.75,1.55,14)
text(s,"사용자마다 자체 랜덤 결과를 만들지 않아 모든 화면의 우승자가 일치",6.7,6.25,5.65,.4,14,WHITE,True)

# 8. AI quiz
s=base("근거 기반 AI 퀴즈 파이프라인", "07 · GENERATIVE AI", 8)
add_image(s,GAME/"LLM WIKI  를기반으로 OPenAI 가문제를 출제 하는 화면.png",.6,1.5,4.2,4.9)
flow=[("WIKI","Markdown 발췌",MINT),("GENERATE","Responses API",PINK),("STRUCTURE","JSON Schema",YELLOW),("VALIDATE","출처·정답 검증",BLUE),("STORE","MySQL 재사용",MINT)]
for i,(a,b,c) in enumerate(flow):
    x=5.05+i*1.48; rect(s,x,1.55,1.28,1.12,PANEL,c); text(s,a,x+.08,1.82,1.12,.18,10,c,True,"Arial",PP_ALIGN.CENTER); text(s,b,x+.08,2.16,1.12,.24,9,WHITE,False,"Arial",PP_ALIGN.CENTER)
    if i<4:text(s,"→",x+1.25,1.9,.25,.3,14,MUTED,True,"Arial",PP_ALIGN.CENTER)
code(s,'아래 LLM Wiki 발췌문만 근거로\n한국어 프로그래밍 퀴즈 한 문제를 만들어라.\n\n"choices": { "minItems": 2, "maxItems": 4 },\n"answer":  { "minimum": 0, "maximum": 3 }\n\nif (excerpts.noneMatch(q.source()))\n    throw new IllegalArgumentException("출처 불일치");',5.05,3.02,7.35,3.38,"PROMPT → SCHEMA → SERVER VALIDATION")
text(s,"AI 생성 OFF 시 검증된 저장 문제로 자동 대체",8.0,6.57,4.4,.28,12,YELLOW,True,"Arial",PP_ALIGN.RIGHT)

# 9. Other games
s=base("게임 규칙을 상태 머신으로 확장", "08 · GAME CONTENT", 9)
add_image(s,GAME/"낮시 간채팅으로 소통.png",.65,1.5,3.9,4.35)
add_image(s,GAME/"행맨 진행.png",4.75,1.5,3.9,4.35)
add_image(s,GAME/"문제 정답 화면 .png",8.85,1.5,3.8,4.35)
text(s,"마피아",.65,6.02,3.9,.25,15,PINK,True,align=PP_ALIGN.CENTER); text(s,"게임 상태에 종속된 낮/밤 전용 채팅",.65,6.38,3.9,.25,11,MUTED,align=PP_ALIGN.CENTER)
text(s,"1:1 행맨",4.75,6.02,3.9,.25,15,YELLOW,True,align=PP_ALIGN.CENTER); text(s,"라운드 · 피해량 · 승패 판정",4.75,6.38,3.9,.25,11,MUTED,align=PP_ALIGN.CENTER)
text(s,"위키 퀴즈",8.85,6.02,3.8,.25,15,MINT,True,align=PP_ALIGN.CENTER); text(s,"문제 · 해설 · 출처 · 보상",8.85,6.38,3.8,.25,11,MUTED,align=PP_ALIGN.CENTER)

# 10. Character
s=base("시간 기반 2D 캐릭터 컨트롤", "09 · ANIMATION", 10)
add_image(s,GAME/"캐릭터 조작 테스트.png",.65,1.5,6.15,4.95)
code(s,"const dt = Math.min((now - previous) / 1000, 0.032);\nconst velocity = running ? RUN_SPEED : WALK_SPEED;\n\nx += direction * velocity * dt;\nvy -= GRAVITY * dt;\ny  += vy * dt;\n\nif (landingOnPlatform) {\n  y = platformTop; vy = 0; grounded = true;\n}\nraf = requestAnimationFrame(tick);",7.15,1.5,5.5,3.85,"REQUESTANIMATIONFRAME + ΔT")
rich_lines(s,[("INPUT  ","방향키 · Shift 달리기 · 점프",MINT),("PHYSICS  ","중력 · 수직 속도 · 발판 착지",PINK),("STATE  ","idle / walk / run / jump 전환",YELLOW)],7.15,5.65,5.2,1.1,13)

# 11. Social/admin
s=base("공용 채팅과 크레딧 운영 시스템", "10 · OPERATIONS", 11)
add_image(s,GAME/"채팅화면.png",.65,1.48,3.65,4.7)
add_image(s,GAME/"관리자 페이지 플레이어 점수 관리 및 AI문제 출제 활성화 버튼.png",4.55,1.48,4.55,4.7)
code(s,"String clean = text.strip();\nif (clean.isBlank() || clean.length() > 200)\n    throw new IllegalArgumentException(...);\n\nchat.addLast(message);\nwhile (chat.size() > 80) chat.removeFirst();\n\n@Transactional\nvoid grantCredits(Player p, long amount) { ... }",9.35,1.48,3.3,3.42,"VALIDATE · LIMIT · TRANSACTION")
rich_lines(s,[("공용 채팅  ","게임 종류와 무관한 최근 80개 메시지",MINT),("마피아 채팅  ","낮/밤·역할 상태에 따라 별도 접근 제어",BLUE),("관리자  ","코드 인증 · 지급/차감 · 퇴장",PINK)],9.35,5.02,3.2,1.72,11.5)

# 12. Reliability
s=base("서버 중심 상태 관리", "11 · RELIABILITY", 12)
problems=[("동시 요청","GameCommandQueue + synchronized","턴과 공유 상태 변경을 순서대로 처리",PINK),("데이터 일관성","@Transactional","참가비 차감과 보상 지급을 원자적으로 처리",MINT),("클라이언트 조작","서버 재검증","턴·주사위·참가 금액·관리자 요청 검증",YELLOW),("유령 참가자","활동 시간 정리","비활성 사용자를 주기적으로 제거",BLUE)]
for i,(p,sol,desc,c) in enumerate(problems):
    y=1.48+i*1.28; rect(s,.75,y,2.35,.92,PANEL,c); text(s,p,.95,y+.28,1.95,.25,15,c,True,align=PP_ALIGN.CENTER)
    text(s,"→",3.25,y+.2,.5,.4,24,MUTED,True,"Arial",PP_ALIGN.CENTER)
    rect(s,3.85,y,3.1,.92,PANEL2,LINE); text(s,sol,4.05,y+.25,2.7,.28,14,WHITE,True,"Consolas",PP_ALIGN.CENTER)
    rect(s,7.2,y,5.25,.92,PANEL,LINE); text(s,desc,7.48,y+.25,4.7,.32,13,WHITE,False)
text(s,"핵심 원칙  ·  화면의 상태보다 서버의 상태를 신뢰한다",3.15,6.72,7.0,.3,15,MINT,True,"Arial",PP_ALIGN.CENTER)

# 13. Testing
s=base("검증 가능한 게임 규칙", "12 · TESTING", 13)
code(s,'@Test\nvoid yachtScoresAreCalculatedByRule() {\n  assertEquals(50, calculate("YACHT", 6,6,6,6,6));\n  assertEquals(30, calculate("LARGE_STRAIGHT", 1,2,3,4,5));\n}\n\n@Test\nvoid mafiaNightAndVoteFlowIsDeterministic() {\n  // 역할, 제거, 승리 조건을 단계별 검증\n}',.7,1.55,5.65,4.9,"JUNIT · DOMAIN RULE TEST")
rect(s,6.7,1.55,5.9,4.9,PANEL,LINE)
text(s,"테스트 대상",7.05,1.9,2.2,.3,17,MINT,True)
rich_lines(s,[("야추 점수  ","12개 카테고리와 스트레이트·보너스",MINT),("마피아 흐름  ","역할 배정·낮/밤·투표·승리 조건",PINK),("서버 검증  ","잘못된 턴과 중복 요청 거부",YELLOW)],7.05,2.45,5.0,2.0,15)
text(s,"확장 계획",7.05,4.9,2.2,.3,17,BLUE,True)
text(s,"Controller 통합 테스트 · 동시성 테스트 · 프론트 UI 테스트",7.05,5.4,4.9,.7,14,WHITE,True)

# 14. Learning
s=base("Troubleshooting & Learning", "13 · RETROSPECTIVE", 14)
items=[("사용자별 결과 불일치","랜덤 판정을 서버에서 한 번만 수행",MINT),("턴·크레딧 충돌","명령 큐 + 동기화 + 트랜잭션",PINK),("LLM 형식·근거 오류","근거 제한 + JSON Schema + 서버 검증",YELLOW),("환경별 이동 속도 차이","프레임 시간 차이 dt 적용",BLUE)]
for i,(a,b,c) in enumerate(items):
    x=.7+(i%2)*6.15; y=1.55+(i//2)*2.25
    rect(s,x,y,5.8,1.75,PANEL,c); text(s,f"0{i+1}",x+.25,y+.25,.55,.3,14,c,True,"Arial"); text(s,a,x+.95,y+.22,4.45,.35,17,WHITE,True); text(s,b,x+.95,y+.83,4.45,.45,14,MUTED)
rect(s,1.55,6.15,10.2,.62,PANEL2,MINT); text(s,"기능을 만드는 것에서 끝내지 않고, 신뢰 가능한 서비스 상태를 설계하는 경험",1.75,6.35,9.8,.25,15,WHITE,True,align=PP_ALIGN.CENTER)

# 15. Result
s=base("Result", "22 · OUTCOME", 23)
imgs=["야추게임화면.png","달팽이 레이싱 종료 화면.png","문제 정답 화면 .png","캐릭터 조작 테스트.png","관리자 페이지 플레이어 점수 관리 및 AI문제 출제 활성화 버튼.png"]
for i,name in enumerate(imgs):
    add_image(s,GAME/name,.6+i*2.48,1.42,2.25,2.48)
metrics=[("6","MAX PLAYERS"),("5+","GAME CONTENTS"),("1","SHARED CREDIT"),("100%","PERSONAL BUILD")]
for i,(n,lbl) in enumerate(metrics):
    x=.75+i*3.05; rect(s,x,4.35,2.7,1.25,PANEL,LINE); text(s,n,x+.15,4.57,2.4,.42,25,[MINT,PINK,YELLOW,BLUE][i],True,"Arial",PP_ALIGN.CENTER); text(s,lbl,x+.15,5.12,2.4,.2,9,MUTED,True,"Arial",PP_ALIGN.CENTER)
text(s,"게임 · 실시간 상태 · AI · 운영 기능을 하나의 풀스택 서비스로 통합",1.4,6.15,10.5,.42,19,WHITE,True,align=PP_ALIGN.CENTER)
text(s,"THANK YOU",4.8,6.73,3.7,.3,15,MINT,True,"Arial",PP_ALIGN.CENTER)
result_slide = s
result_id = prs.slides._sldIdLst[-1]

# 16. Request traffic model
s=base("반복 요청이 만드는 서버 부하", "DEEP DIVE · REQUEST TRAFFIC", 15)
rect(s,.65,1.48,4.0,4.9,PANEL,LINE)
text(s,"현재 통신 모델",.95,1.82,3.3,.35,19,MINT,True)
rich_lines(s,[("게임 상태  ","/api/state · 1초마다",MINT),("소셜 상태  ","/api/social/state · 1초마다",PINK),("마피아 상태  ","참여 중 추가 조회",YELLOW),("관리자  ","2초마다 2개 운영 API 조회",BLUE)],.95,2.4,3.3,2.3,14)
text(s,"최대 6명 기준",.95,5.12,3.2,.3,14,MUTED,True)
text(s,"기본 약 12 read req/s",.95,5.55,3.2,.4,21,WHITE,True,"Arial")
text(s,"※ 계산값이며 부하 테스트 측정치는 아님",.95,6.02,3.2,.2,9,MUTED)
flow=[("READ","상태 조회","병렬 처리",MINT),("COMMAND","게임 행동","큐 진입",PINK),("DB WRITE","크레딧·문제","트랜잭션",YELLOW)]
for i,(a,b,detail,c) in enumerate(flow):
    x=5.15+i*2.5; rect(s,x,1.7,2.1,1.28,PANEL,c); text(s,a,x+.12,1.98,1.86,.22,12,c,True,"Arial",PP_ALIGN.CENTER); text(s,b,x+.12,2.4,1.86,.2,11,WHITE,False,"Arial",PP_ALIGN.CENTER)
    if i<2:text(s,"→",x+2.1,2.1,.4,.3,17,MUTED,True,"Arial",PP_ALIGN.CENTER)
code(s,"// 상태 조회는 큐를 거치지 않음\n@GetMapping(\"/state\")\nObject state(...) { return service.state(player); }\n\n// 상태 변경 명령만 순차 처리\n@PostMapping(\"/yacht/score\")\nObject score(...) {\n  return queue.run(() -> social.score(...));\n}",5.15,3.4,7.5,2.98,"READ / WRITE PATH SEPARATION")
text(s,"핵심: 모든 요청을 직렬화하지 않고, 충돌 위험이 큰 상태 변경 명령을 통제",5.15,6.55,7.45,.3,13,WHITE,True)

# 17. Queue
s=base("명령 큐로 순서와 과부하를 통제", "DEEP DIVE · COMMAND QUEUE", 16)
code(s,"new ThreadPoolExecutor(\n  1, 1, 0L, MILLISECONDS,\n  new ArrayBlockingQueue<>(128),\n  threadFactory,\n  new AbortPolicy()\n);\n\nreturn CompletableFuture\n  .supplyAsync(command, executor).join();",.7,1.5,5.3,4.85,"GAMECOMMANDQUEUE.JAVA")
steps=[("①","단일 Worker","게임 명령 실행 순서 보장",MINT),("②","Bounded 128","무제한 적재로 인한 메모리 증가 방지",PINK),("③","Abort Policy","포화 시 즉시 거절하고 재시도 안내",YELLOW),("④","Exception unwrap","도메인 오류를 원래 메시지로 반환",BLUE)]
for i,(n,a,b,c) in enumerate(steps):
    y=1.5+i*1.22; rect(s,6.35,y,6.25,.94,PANEL,LINE); text(s,n,6.55,y+.27,.45,.25,14,c,True,"Arial"); text(s,a,7.1,y+.21,1.65,.25,14,WHITE,True); text(s,b,8.75,y+.22,3.55,.32,12,MUTED)
rect(s,6.35,6.42,6.25,.48,PANEL2,PINK); text(s,"Trade-off · 처리량보다 작은 LAN 환경의 상태 일관성을 우선",6.55,6.57,5.85,.2,11,WHITE,True,align=PP_ALIGN.CENTER)

# 18. Transactions
s=base("트랜잭션 경계를 게임 결과와 맞추다", "DEEP DIVE · TRANSACTION", 17)
text(s,"예: 야추 점수 확정과 크레딧 정산",.75,1.55,4.3,.35,18,YELLOW,True)
timeline=[("검증","현재 턴·주사위·카테고리"),("계산","서버 주사위로 점수 산출"),("상태","점수표·다음 턴 갱신"),("정산","우승자 크레딧 저장")]
for i,(a,b) in enumerate(timeline):
    x=.7+i*3.05; c=[MINT,PINK,YELLOW,BLUE][i]; rect(s,x,2.15,2.55,1.25,PANEL,c); text(s,a,x+.15,2.43,2.25,.25,15,c,True,align=PP_ALIGN.CENTER); text(s,b,x+.15,2.82,2.25,.3,11,WHITE,align=PP_ALIGN.CENTER)
    if i<3:text(s,"→",x+2.55,2.52,.5,.35,20,MUTED,True,"Arial",PP_ALIGN.CENTER)
code(s,"@Transactional\npublic synchronized Map<String,Object> score(...) {\n  YachtGame g = activeTurn(player);\n  validateDiceAndCategory(g, request);\n  sheet.put(category, calculate(category, g.dice));\n  if (finished) finishYacht(g); // repo.save(winner)\n  else advanceTurn(g);\n  return state(player);\n}",.7,3.85,6.0,2.72,"APPLICATION TRANSACTION BOUNDARY")
rich_lines(s,[("원자성  ","예외 발생 시 DB 변경 롤백",MINT),("일관성  ","허용 금액과 잔액을 도메인에서 검증",PINK),("격리 보완  ","명령 큐 + synchronized로 인메모리 경쟁 제어",YELLOW),("주의  ","인메모리 상태는 DB 롤백 대상이 아니므로 확장 시 영속 상태화 필요",BLUE)],7.05,3.92,5.25,2.55,13)

# 19. Failure scenario
s=base("실패 시나리오로 보는 데이터 일관성", "DEEP DIVE · FAILURE HANDLING", 18)
scenarios=[("동시 참가","두 사용자가 마지막 크레딧으로 동시에 참가","큐가 명령을 순차 실행 → 두 번째 요청은 최신 잔액으로 재검증",MINT),("중복 점수","같은 야추 항목을 연속 클릭","사용 완료 카테고리 검사 → 두 번째 요청 거절",PINK),("정산 중 예외","우승자 저장 중 DB 오류","@Transactional 롤백 → 일부 사용자만 지급되는 상태 방지",YELLOW),("큐 포화","128개를 넘는 변경 요청 유입","AbortPolicy → 빠른 실패와 ‘잠시 후 재시도’ 응답",BLUE)]
for i,(a,b,c,d) in enumerate(scenarios):
    y=1.48+i*1.29; rect(s,.68,y,2.0,.95,PANEL,d); text(s,a,.83,y+.3,1.7,.25,14,d,True,align=PP_ALIGN.CENTER)
    rect(s,2.92,y,3.75,.95,PANEL,LINE); text(s,b,3.18,y+.24,3.25,.42,12,WHITE,True)
    text(s,"→",6.72,y+.25,.4,.35,19,MUTED,True,"Arial",PP_ALIGN.CENTER)
    rect(s,7.2,y,5.45,.95,PANEL2,LINE); text(s,c,7.48,y+.22,4.9,.48,12,MUTED)
text(s,"설계 의도: 성공 경로보다 ‘동시에 요청되거나 중간에 실패했을 때’의 상태를 먼저 정의",1.4,6.68,10.5,.28,14,WHITE,True,align=PP_ALIGN.CENTER)

# 20. Scale roadmap
s=base("현재 구조의 한계와 확장 전략", "DEEP DIVE · SCALABILITY", 19)
left=[("대상","동일 LAN · 최대 6명"),("동기화","1초 폴링"),("상태","단일 서버 메모리"),("명령","단일 Worker Queue")]
right=[("실시간 통신","WebSocket / SSE"),("분산 상태","Redis + 세션 공유"),("동시성","DB Lock / Optimistic Lock"),("처리량","게임 Room별 파티셔닝")]
rect(s,.7,1.5,5.55,4.95,PANEL,LINE); text(s,"현재 선택",1.0,1.83,2.2,.35,19,MINT,True)
rect(s,7.05,1.5,5.55,4.95,PANEL,LINE); text(s,"확장 단계",7.35,1.83,2.2,.35,19,PINK,True)
for i,(a,b) in enumerate(left):
    text(s,a,1.05,2.55+i*.8,1.3,.25,13,MUTED,True); text(s,b,2.4,2.55+i*.8,3.2,.3,14,WHITE,True)
for i,(a,b) in enumerate(right):
    text(s,a,7.4,2.55+i*.8,1.45,.25,13,MUTED,True); text(s,b,8.9,2.55+i*.8,3.1,.3,14,WHITE,True)
text(s,"현재 요구사항에는 단순성과 일관성이 유리하지만, 수평 확장 시 인메모리 상태와 단일 큐가 병목",1.2,6.72,10.95,.28,13,YELLOW,True,align=PP_ALIGN.CENTER)

# 21. AI generation
s=base("AI 문제 출제: 근거를 먼저 고정", "DEEP DIVE · AI GENERATION", 20)
add_image(s,GAME/"LLM WIKI  를기반으로 OPenAI 가문제를 출제 하는 화면.png",.65,1.5,4.05,4.95)
code(s,"List<WikiExcerpt> excerpts = pickExcerpts(3);\n\n아래 LLM Wiki 발췌문만 근거로\n한국어 프로그래밍 퀴즈 한 문제를 만들어라.\n사실이 애매하거나 발췌문으로 검증할 수 없는\n내용은 묻지 마라.\nsource는 제공된 SOURCE 경로를 그대로 사용한다.",4.98,1.5,4.25,3.08,"GROUNDING PROMPT")
rich_lines(s,[("문서 선택  ","_meta·index·log 제외 후 Markdown 3개 무작위 선택",MINT),("길이 제한  ","발췌문 크기를 제한해 입력 비용 통제",PINK),("유형 다양화  ","concept·code_output·debugging·scenario·true_false",YELLOW),("최근 이력  ","최근 20개 핵심 문장과 비교해 반복 감소",BLUE)],9.5,1.62,3.0,3.55,11.5)
text(s,"게임을 만든 이유: 문제 풀이 보상을 공통 크레딧과 연결해 AI 기능이 플랫폼 안에서 지속적으로 소비되도록 설계",4.98,5.15,7.5,1.0,14,WHITE,True)

# 22. AI validation
s=base("AI 응답은 서버 검증을 통과해야 한다", "DEEP DIVE · AI VALIDATION", 21)
code(s,'"type": "object",\n"additionalProperties": false,\n"required": ["category", "type", "prompt",\n             "choices", "answer", "explanation", "source"],\n"choices": { "minItems": 2, "maxItems": 4 },\n"answer":  { "minimum": 0, "maximum": 3 }',.7,1.5,5.45,3.35,"STRUCTURED OUTPUTS · JSON SCHEMA")
code(s,"if (choices.size() < 2 || choices.size() > 4)\n    throw new IllegalArgumentException(...);\nif (answer < 0 || answer >= choices.size())\n    throw new IllegalArgumentException(...);\nif (excerpts.noneMatch(e -> e.source().equals(source)))\n    throw new IllegalArgumentException(\"출처 불일치\");",6.45,1.5,6.2,3.35,"SECOND VALIDATION · SERVER")
rules=[("형식","필수 필드와 선택지 개수",MINT),("범위","정답 인덱스 유효성",PINK),("근거","허용된 위키 경로 일치",YELLOW),("회복","최대 3회 생성 재시도",BLUE)]
for i,(a,b,c) in enumerate(rules):
    x=.8+i*3.08; rect(s,x,5.35,2.75,1.05,PANEL,c); text(s,a,x+.15,5.59,2.45,.22,14,c,True,align=PP_ALIGN.CENTER); text(s,b,x+.15,5.98,2.45,.2,10.5,WHITE,align=PP_ALIGN.CENTER)

# 23. AI storage and transaction
s=base("설명과 출처까지 저장해 서비스 자산으로", "DEEP DIVE · AI PERSISTENCE", 22)
code(s,"@Entity @Table(\n  name = \"quiz_questions\",\n  uniqueConstraints = @UniqueConstraint(columnNames=\"signature\")\n)\nclass QuizQuestionEntity {\n  String prompt; List<String> choices; int answerIndex;\n  String explanation; String source; Instant createdAt;\n}",.7,1.5,5.2,4.75,"QUIZQUESTIONENTITY")
flow2=[("생성","문제·정답·설명·출처",MINT),("정규화","문장 signature 생성",PINK),("중복 확인","findBySignature",YELLOW),("저장","문제 + 선택지 테이블",BLUE),("재사용","AI OFF 시 DB에서 출제",MINT)]
for i,(a,b,c) in enumerate(flow2):
    y=1.48+i*1.02; rect(s,6.25,y,2.05,.76,PANEL,c); text(s,a,6.4,y+.24,1.75,.2,13,c,True,align=PP_ALIGN.CENTER); text(s,"→",8.35,y+.18,.35,.3,16,MUTED,True,"Arial",PP_ALIGN.CENTER); rect(s,8.72,y,3.85,.76,PANEL2,LINE); text(s,b,8.95,y+.21,3.4,.28,12,WHITE,True)
text(s,"정답 제출도 @Transactional: 활성 문제 ID 확인 → 선택지 검증 → 정답 보상 저장",6.25,6.02,6.25,.42,13,YELLOW,True)
text(s,"생성 비용을 일회성으로 바꾸고, 장애·비활성화 상황에서도 퀴즈 서비스를 유지",3.25,6.7,7.4,.28,14,WHITE,True,align=PP_ALIGN.CENTER)

# Planning background — make the engineering intent explicit.
planning_slide = base("기획 배경: 게임보다 상태 변화가 많은 서비스", "01 · Planning background", 4)
text(planning_slide, "출발점", .75, 1.52, 1.2, .28, 12, MINT, True)
text(planning_slide, "게임은 짧은 시간에 ‘참가 → 차감 → 판정 → 정산’이 반복됩니다.", 2.05, 1.45, 9.8, .58, 17, WHITE, True)
rect(planning_slide, .75, 2.32, 11.55, .012, LINE, LINE, False)
planning_cols = [
    ("기획 의도", "반복되는 크레딧 변화와 게임 상태 전이를 통해 트랜잭션, 동시 요청, 상태 동기화를 구현하고자 했습니다.", MINT),
    ("핵심 문제", "여러 사용자의 요청이 같은 시점에 도착해도 중복 차감과 서로 다른 결과가 발생하지 않아야 합니다.", BLUE),
    ("최종 범위", "레이싱·야추·행맨·마피아가 하나의 플레이어와 크레딧을 공유하며 서버가 결과를 최종 판정합니다.", YELLOW),
]
for i, (head, body, c) in enumerate(planning_cols):
    x = .75 + i * 3.9
    text(planning_slide, f"0{i+1}", x, 2.72, .4, .25, 11, c, True, "Arial")
    text(planning_slide, head, x, 3.12, 3.45, .35, 17, WHITE, True)
    text(planning_slide, body, x, 3.72, 3.45, 1.35, 13.5, MUTED)
text(planning_slide, "서비스 경계", .75, 5.65, 1.3, .25, 12, PINK, True)
text(planning_slide, "크레딧은 서비스 내부에서만 사용하는 게임 점수이며, 동일 LAN 최대 6명을 실제 목표 범위로 설정", 2.15, 5.58, 9.8, .38, 14, WHITE, True)
text(planning_slide, "핵심 질문  ·  두 사용자가 동시에 마지막 크레딧으로 참가하면 서버 상태는 어떻게 설명되어야 하는가?", .75, 6.48, 11.55, .42, 15, BLUE, True, align=PP_ALIGN.CENTER)
planning_id = prs.slides._sldIdLst[-1]

# Credit lifecycle and transaction boundary.
economy_slide = base("크레딧 정산의 전체 생명주기", "03 · Credit lifecycle", 7)
stages = [
    ("1", "요청", "player · game · stake", MINT),
    ("2", "검증", "잔액 · 허용 금액 · 중복", BLUE),
    ("3", "차감", "Player.debit + save", YELLOW),
    ("4", "진행", "참가자·턴·pot 상태", PINK),
    ("5", "판정", "서버 결과 단일 생성", BLUE),
    ("6", "정산", "winner.credit + save", MINT),
]
for i, (n, head, body, c) in enumerate(stages):
    x = .55 + i * 2.08
    text(economy_slide, n, x, 1.55, .32, .28, 11, c, True, "Arial")
    text(economy_slide, head, x, 1.92, 1.72, .3, 16, WHITE, True)
    text(economy_slide, body, x, 2.38, 1.72, .56, 11.5, MUTED)
    if i < 5: text(economy_slide, "→", x + 1.72, 2.0, .34, .3, 16, MUTED, True, "Arial", PP_ALIGN.CENTER)
rect(economy_slide, .7, 3.32, 5.85, 2.65, PANEL, LINE)
text(economy_slide, "DB 트랜잭션 안에서 보장", 1.0, 3.63, 4.9, .3, 17, MINT, True)
rich_lines(economy_slide, [
    ("원자성  ", "차감·보상 저장 중 예외가 발생하면 DB 변경 롤백", MINT),
    ("검증  ", "허용 stake와 현재 잔액을 서버 값으로 다시 확인", BLUE),
    ("정산  ", "게임별 참가비와 보상을 동일 Player 크레딧으로 통합", YELLOW),
], 1.0, 4.18, 5.0, 1.45, 12.5)
rect(economy_slide, 6.82, 3.32, 5.8, 2.65, PANEL, LINE)
text(economy_slide, "DB 트랜잭션만으로 부족한 부분", 7.12, 3.63, 5.0, .3, 17, PINK, True)
rich_lines(economy_slide, [
    ("메모리 상태  ", "턴·참가자·pot은 JPA 롤백 대상이 아님", PINK),
    ("경쟁 조건  ", "명령 큐와 synchronized로 변경 순서를 통제", BLUE),
    ("확장 시  ", "Redis/DB 상태화와 낙관적 락·멱등 키가 필요", YELLOW),
], 7.12, 4.18, 5.0, 1.45, 12.5)
text(economy_slide, "한 번의 게임 사건이 어디서 시작하고 어디까지 함께 성공해야 하는지를 트랜잭션 경계로 정의", 1.05, 6.55, 11.2, .35, 14, WHITE, True, align=PP_ALIGN.CENTER)
economy_id = prs.slides._sldIdLst[-1]

# Concrete concurrency sequence.
concurrency_slide = base("동시에 들어온 참가 요청을 어떻게 처리했는가", "Deep dive · Concurrency", 21)
text(concurrency_slide, "상황: A와 B가 거의 동시에 마지막 크레딧으로 참가", .75, 1.48, 8.6, .35, 17, WHITE, True)
actors = [("Client A", .85, MINT), ("Client B", .85, BLUE), ("Command Queue", 4.75, YELLOW), ("Service / DB", 8.72, PINK)]
for idx, (name, x, c) in enumerate(actors):
    y = 2.0 if idx != 1 else 2.92
    rect(concurrency_slide, x, y, 3.05, .65, PANEL, c)
    text(concurrency_slide, name, x + .18, y + .2, 2.7, .24, 13, c, True, "Arial", PP_ALIGN.CENTER)
text(concurrency_slide, "POST join(A)", 1.0, 3.94, 2.7, .25, 12, WHITE, True)
text(concurrency_slide, "POST join(B)", 1.0, 4.62, 2.7, .25, 12, WHITE, True)
text(concurrency_slide, "① enqueue", 3.55, 3.94, 1.1, .25, 11, MUTED)
text(concurrency_slide, "② enqueue", 3.55, 4.62, 1.1, .25, 11, MUTED)
rect(concurrency_slide, 4.75, 3.72, 3.05, 1.35, PANEL2, LINE)
text(concurrency_slide, "A 실행 완료 후 B 실행", 5.0, 4.14, 2.55, .42, 14, WHITE, True, align=PP_ALIGN.CENTER)
text(concurrency_slide, "③ 최신 잔액 검증", 7.85, 3.94, 1.25, .25, 11, MUTED)
text(concurrency_slide, "④ B 재검증", 7.85, 4.62, 1.25, .25, 11, MUTED)
rect(concurrency_slide, 9.15, 3.72, 3.0, 1.35, PANEL, LINE)
text(concurrency_slide, "A: 차감 성공\nB: 잔액 부족 거절", 9.4, 4.0, 2.5, .65, 14, WHITE, True, align=PP_ALIGN.CENTER)
text(concurrency_slide, "순서 보장", .85, 5.72, 1.2, .25, 12, MINT, True)
text(concurrency_slide, "단일 Worker Queue", 2.08, 5.68, 2.2, .3, 13, WHITE, True)
text(concurrency_slide, "임계 구역", 4.48, 5.72, 1.2, .25, 12, BLUE, True)
text(concurrency_slide, "synchronized service", 5.72, 5.68, 2.25, .3, 13, WHITE, True)
text(concurrency_slide, "DB 원자성", 8.25, 5.72, 1.2, .25, 12, YELLOW, True)
text(concurrency_slide, "@Transactional", 9.48, 5.68, 2.2, .3, 13, WHITE, True)
text(concurrency_slide, "현재 선택은 처리량보다 설명 가능한 상태를 우선하며, 확장 시 Room별 큐로 병렬성을 확보", 1.05, 6.58, 11.2, .34, 14, PINK, True, align=PP_ALIGN.CENTER)
concurrency_id = prs.slides._sldIdLst[-1]

# Promotion UI evidence using the newly supplied photo.
ad_slide = base("외부 프로모션을 서비스 UI에 연결", "Feature · Promotion", 15)
add_image(ad_slide, GAME / "배너광고 이미지.png", .7, 1.48, 5.7, 1.18)
add_image(ad_slide, ROOT / "모달광고.png", .7, 2.88, 5.7, 3.98)
text(ad_slide, "배너 + 세션 모달 광고", 6.82, 1.55, 5.25, .4, 20, WHITE, True)
text(ad_slide, "실제 브라우저에서 캡처한 배너와 모달 화면을 원본 비율로 배치했습니다.", 6.82, 2.08, 5.25, .58, 13.5, MUTED)
rich_lines(ad_slide, [
    ("소재  ", "로컬 image1·image2를 사용해 외부 이미지 만료 방지", MINT),
    ("노출  ", "배너는 상시, 모달은 sessionStorage 기준 세션당 1회", BLUE),
    ("반응형  ", "원본 1:1 비율 유지, 화면 높이에 맞춰 최대 크기 제한", YELLOW),
    ("이동  ", "원본 Instagram 게시물 링크를 새 탭으로 연결", PINK),
    ("접근성  ", "대체 텍스트·닫기 버튼·dialog 속성 적용", MINT),
], 6.82, 2.95, 5.15, 2.75, 12.5)
text(ad_slide, "게임 기능 외에도 실제 서비스에서 필요한 콘텐츠 노출과 외부 캠페인 연결 흐름을 구현", 6.82, 6.18, 5.15, .58, 14, WHITE, True)
ad_id = prs.slides._sldIdLst[-1]

# Measured concurrency result — evidence for the design claims.
load_test_slide = base("최대 6명 동시 요청 검증 결과", "Validation · Measured result", 23)
add_image(load_test_slide, ROOT / "부하테스트 이미지.png", .7, 1.48, 7.25, 1.88)
rect(load_test_slide, 8.28, 1.48, 4.32, 1.88, PANEL, LINE)
text(load_test_slide, "FINAL RESULT", 8.58, 1.78, 3.7, .22, 10, MUTED, True, "Arial")
text(load_test_slide, "PASS", 8.58, 2.15, 3.7, .48, 28, MINT, True, "Arial")
text(load_test_slide, "동일 LAN 최대 6명 요구사항 기준", 8.58, 2.74, 3.5, .25, 11.5, MUTED)
results = [
    ("6 / 6", "동시 입장 성공", MINT),
    ("6 / 6", "야추 동시 참가", BLUE),
    ("5 / 5", "중복 요청 거절", YELLOW),
    ("60 / 60", "상태 조회 성공", PINK),
]
for i, (value, label, c) in enumerate(results):
    x = .72 + i * 3.0
    rect(load_test_slide, x, 3.72, 2.72, 1.18, PANEL, LINE)
    text(load_test_slide, value, x + .16, 3.94, 2.4, .36, 22, c, True, "Arial", PP_ALIGN.CENTER)
    text(load_test_slide, label, x + .16, 4.48, 2.4, .22, 11, MUTED, True, align=PP_ALIGN.CENTER)
text(load_test_slide, "응답 시간", .75, 5.38, 1.2, .25, 13, WHITE, True)
latencies = [("평균", "30.37 ms"), ("p95", "79.85 ms"), ("최대", "107.17 ms"), ("실패", "0건")]
for i, (label, value) in enumerate(latencies):
    x = 2.1 + i * 2.45
    text(load_test_slide, label, x, 5.38, .72, .24, 11, MUTED, True)
    text(load_test_slide, value, x + .72, 5.34, 1.55, .3, 14, WHITE, True, "Arial")
text(load_test_slide, "검증 조건", .75, 6.08, 1.2, .25, 12, BLUE, True)
text(load_test_slide, "6명 동시 참가 시 전원 100 크레딧 1회만 차감 · 동일 사용자 중복 참가 5건 전부 거절", 2.1, 6.02, 10.15, .38, 13.5, WHITE, True)
text(load_test_slide, "※ 대규모 부하 성능이 아니라 실제 목표 범위의 동시성·일관성 검증", .75, 6.66, 11.5, .25, 11, MUTED, False, align=PP_ALIGN.CENTER)
load_test_id = prs.slides._sldIdLst[-1]

# Test harness implementation — show how the measured result was produced.
test_code_slide = base("Python으로 반복 가능한 동시 요청 테스트 구성", "Validation · Test harness", 24)
code(test_code_slide, '''def parallel(jobs, workers=12):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(call, *job) for job in jobs]
        return [future.result() for future in futures]

# 6명의 참가 요청을 동시에 전송
yacht_jobs = [
    (base_url, "/api/yacht/join", token, {"bet": 100})
    for token in tokens
]
yacht_responses = parallel(yacht_jobs, workers=6)

join_success = sum(r.ok for r in yacht_responses)
credits_once = all(
    state.data["me"]["credits"]
      == initial_credits[state.data["me"]["id"]] - 100
    for state in after_join_states
)''', .7, 1.48, 6.05, 4.95, "CONCURRENT REQUEST · VERIFICATION")
steps = [
    ("01", "동시 시작", "ThreadPoolExecutor로 6개의 HTTP 요청을 병렬 전송", MINT),
    ("02", "결과 확인", "응답 성공 수, 야추 로비 인원과 최종 크레딧 비교", BLUE),
    ("03", "중복 검증", "같은 토큰의 참가 요청 5건을 보내 모두 거절되는지 확인", YELLOW),
    ("04", "조회 측정", "상태 API 60건의 성공률과 평균·p95·최대 시간 집계", PINK),
    ("05", "보고서 저장", "실행 조건과 결과를 Markdown으로 자동 기록", MINT),
]
for i, (n, head, body, c) in enumerate(steps):
    y = 1.5 + i * 1.02
    text(test_code_slide, n, 7.12, y + .14, .42, .22, 11, c, True, "Arial")
    text(test_code_slide, head, 7.72, y + .1, 1.45, .28, 14, WHITE, True)
    text(test_code_slide, body, 9.25, y + .08, 3.15, .48, 11.5, MUTED)
    rect(test_code_slide, 7.12, y + .73, 5.25, .012, LINE, LINE, False)
text(test_code_slide, "실행", .72, 6.67, .6, .22, 11, BLUE, True)
text(test_code_slide, "python scripts/local_arcade_concurrency_test.py --join-code <6자리 코드>", 1.4, 6.62, 7.1, .28, 11.5, WHITE, True, "Consolas")
text(test_code_slide, "산출물  reports/local-arcade-concurrency-*.md", 8.65, 6.62, 3.7, .28, 10.5, MUTED, False, "Consolas", PP_ALIGN.RIGHT)
test_code_id = prs.slides._sldIdLst[-1]

# Communication model: distinguish the implemented transport from the scale-up design.
communication_slide = base("통신 구조: 현재 구현과 확장 경계", "DEEP DIVE · COMMUNICATION", 17)
rect(communication_slide, .7, 1.5, 5.65, 4.9, PANEL, LINE)
text(communication_slide, "현재 구현 · HTTP Polling", 1.0, 1.82, 4.9, .35, 19, MINT, True)
rich_lines(communication_slide, [
    ("Transport  ", "TCP/IP 위의 HTTP REST", MINT),
    ("Sync  ", "클라이언트가 1초마다 상태 조회", BLUE),
    ("Command  ", "사용자 행동은 POST 요청으로 즉시 전달", YELLOW),
    ("장점  ", "구현·복구가 단순하고 최대 6명 요구에 충분", MINT),
    ("비용  ", "변화가 없어도 반복 요청과 응답 발생", PINK),
], 1.0, 2.42, 4.9, 3.25, 13)
rect(communication_slide, 6.75, 1.5, 5.85, 4.9, PANEL, LINE)
text(communication_slide, "확장 설계 · WebSocket", 7.05, 1.82, 4.9, .35, 19, BLUE, True)
rich_lines(communication_slide, [
    ("Connection  ", "초기 Upgrade 후 양방향 연결 유지", BLUE),
    ("Push  ", "상태 변경 이벤트를 Room 구독자에게 전파", MINT),
    ("Partition  ", "게임 Room별 채널과 명령 처리 분리", YELLOW),
    ("Scale-out  ", "Redis Pub/Sub로 서버 간 이벤트 공유", PINK),
    ("운영 과제  ", "재연결·순서·중복·backpressure 처리", BLUE),
], 7.05, 2.42, 4.95, 3.25, 13)
text(communication_slide, "포트폴리오 표기 원칙 · 소켓 통신은 확장 설계이며, 현재 동작은 REST 폴링 기반", 1.25, 6.68, 10.8, .28, 14, WHITE, True, align=PP_ALIGN.CENTER)

# Keep Result as the final slide after the deep-dive section.
slide_ids = prs.slides._sldIdLst
communication_id = slide_ids[-1]
# Remove movable slides first, then insert them at their narrative positions.
for movable in (planning_id, economy_id, concurrency_id, ad_id, load_test_id, test_code_id, communication_id, result_id):
    slide_ids.remove(movable)
slide_ids.insert(3, planning_id)       # after project overview
slide_ids.insert(6, economy_id)        # after architecture
slide_ids.insert(14, ad_id)            # after operations
slide_ids.insert(19, communication_id) # after traffic model
slide_ids.insert(21, concurrency_id)   # after command queue
slide_ids.insert(22, load_test_id)     # measured evidence after concurrency design
slide_ids.insert(23, test_code_id)     # reproducible test implementation
slide_ids.append(result_id)

# Renumber footers after section reordering so the deck feels manually edited
# and no stale generator index remains.
for page, slide in enumerate(prs.slides, 1):
    for shape in slide.shapes:
        if not hasattr(shape, "text_frame"):
            continue
        if shape.text.startswith("Local Arcade  |"):
            shape.text_frame.paragraphs[0].text = f"Local Arcade  |  {page:02d}"
            p = shape.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.RIGHT
            p.font.name = "Arial"; p.font.size = Pt(8); p.font.color.rgb = MUTED

prs.save(OUT)
print(OUT)
