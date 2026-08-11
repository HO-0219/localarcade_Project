import React, { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
type Player = { id: string; nickname: string; credits: number };
type Race = {
  entrants: string[];
  entries: { playerId: string; nickname: string; snail: number; bet: number }[];
  snailCount: number;
  lastResult?: {
    raceId?: number;
    winnerSnail?: number;
    order?: number[];
    winners?: string[];
    multiplier?: number;
  };
};
type Hang = {
  players?: string[];
  names?: string[];
  damage?: number[];
  round?: number;
  word?: string;
  guessed?: string[];
  message?: string;
  done?: boolean;
};
type State = {
  me: Player;
  players: Player[];
  race: Race;
  hangman: Hang;
};
type ChatMessage = {
  id: number;
  nickname: string;
  text: string;
  sentAt: string;
};
type Yacht = {
  lobby: { playerId: string; nickname: string; stake: number }[];
  active?: boolean;
  status?: "PLAYING" | "FINISHED";
  done?: boolean;
  players?: string[];
  names?: string[];
  currentPlayer?: string;
  dice?: number[];
  held?: boolean[];
  rolls?: number;
  scores?: Record<string, Record<string, number>>;
  upperBonuses?: Record<string, number>;
  pot?: number;
  message?: string;
};
type Social = { chat: ChatMessage[]; yacht: Yacht; categories: string[] };
type MafiaPlayer = {
  playerId: string;
  nickname: string;
  alive: boolean;
  role: string;
};
type MafiaState = {
  lobby: { playerId: string; nickname: string; ready: boolean }[];
  active?: boolean;
  done?: boolean;
  players?: MafiaPlayer[];
  phase?: "DAY" | "NIGHT" | "FINISHED";
  round?: number;
  remainingSeconds?: number;
  message?: string;
  myRole?: string;
  myVote?: string;
  myTarget?: string;
  acted?: boolean;
  chat?: ({ scope: string; round: number } & ChatMessage)[];
};
const API = import.meta.env.VITE_API_URL || "",
  letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
const PROMO_POSTS = {
  banner: "https://www.instagram.com/p/Db3TCSsv6Xc/",
  modal: "https://www.instagram.com/p/Dbz6dhjxS4T/",
};
const SNAILS = [
  { name: "아우렐리우스", title: "황금 공작", crest: "♛" },
  { name: "루시엔", title: "월광 백작", crest: "☾" },
  { name: "발렌티노", title: "장미 후작", crest: "⚜" },
  { name: "세라피나", title: "흑요석 공녀", crest: "✦" },
  { name: "레오폴드", title: "폭풍 대공", crest: "♜" },
];
const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

function App() {
  if (location.pathname === "/admin") return <AdminPage />;
  const [token, setToken] = useState(
      localStorage.getItem("arcade-token") || "",
    ),
    [state, setState] = useState<State>(),
    [error, setError] = useState(""),
    [tab, setTab] = useState("race"),
    [promoOpen, setPromoOpen] = useState(
      () => sessionStorage.getItem("arcade-promo-closed") !== "1",
    );
  const [social, setSocial] = useState<Social>(),
    [mafia, setMafia] = useState<MafiaState>(),
    [raceBet, setRaceBet] = useState(500),
    [hangBet, setHangBet] = useState(50),
    [yachtBet, setYachtBet] = useState(100),
    [yachtRolling, setYachtRolling] = useState(false),
    [chosenSnail, setChosenSnail] = useState(1),
    [held, setHeld] = useState([false, false, false, false, false]);
  const [racing, setRacing] = useState(false),
    [countdown, setCountdown] = useState(""),
    [raceOrder, setRaceOrder] = useState<number[]>([]),
    seenRace = useRef(0);
  async function api(path: string, data?: unknown) {
    const r = await fetch(API + path, {
      method: data === undefined ? "GET" : "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: data === undefined ? undefined : JSON.stringify(data),
    });
    const out = await r.json();
    if (!r.ok) throw Error(out.error || "요청 실패");
    return out;
  }
  async function refresh() {
    if (!token) return;
    try {
      const [g, s] = await Promise.all([
        api("/api/state"),
        api("/api/social/state"),
      ]);
      setState(g);
      setSocial(s);
    } catch (e) {
      if ((e as Error).message.includes("다시")) {
        localStorage.removeItem("arcade-token");
        setToken("");
      }
      return;
    }
    try {
      setMafia(await api("/api/mafia/state"));
    } catch {
      setMafia({ lobby: [] });
    }
  }
  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 1000);
    return () => clearInterval(id);
  }, [token]);
  useEffect(() => {
    const result = state?.race.lastResult;
    if (result?.raceId && result.raceId !== seenRace.current) {
      seenRace.current = result.raceId;
      setRaceOrder(result.order || []);
      setRacing(true);
      const id = setTimeout(() => setRacing(false), 10500);
      return () => clearTimeout(id);
    }
  }, [state?.race.lastResult?.raceId]);
  function fail(e: unknown) {
    setError((e as Error).message);
    setTimeout(() => setError(""), 2300);
  }
  async function act(path: string, data: unknown = {}) {
    try {
      const out = await api(path, data);
      if (out.state) setState(out.state);
      return out;
    } catch (e) {
      fail(e);
    }
  }
  async function socialAct(path: string, data: unknown = {}) {
    const rolling = path === "/api/yacht/roll";
    if (rolling) {
      document.body.classList.add("dice-rolling");
      setYachtRolling(true);
    }
    try {
      const [out] = await Promise.all([
        api(path, data),
        rolling ? wait(1550) : Promise.resolve(),
      ]);
      setSocial(out);
      return out;
    } catch (e) {
      fail(e);
    } finally {
      if (rolling) {
        document.body.classList.remove("dice-rolling");
        setYachtRolling(false);
      }
    }
  }
  async function mafiaAct(path: string, data: unknown = {}) {
    try {
      const out = await api(path, data);
      setMafia(out);
      return out;
    } catch (e) {
      fail(e);
    }
  }
  async function join(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      const out = await api("/api/join", {
        code: f.get("code"),
        nickname: f.get("nickname"),
      });
      localStorage.setItem("arcade-token", out.token);
      setToken(out.token);
    } catch (e) {
      fail(e);
    }
  }
  async function changeTab(next: string) {
    if (next === tab) return;
    try {
      if (tab === "yacht") setSocial(await api("/api/yacht/leave", {}));
      else if (tab === "mafia") setMafia(await api("/api/mafia/leave", {}));
      else {
        const out = await api("/api/game/leave", { game: tab });
        setState(out.state);
      }
    } catch {}
    setRaceOrder([]);
    setTab(next);
  }
  async function startRace() {
    if (racing) return;
    setRacing(true);
    setRaceOrder([]);
    for (const n of ["3", "2", "1", "GO!"]) {
      setCountdown(n);
      await wait(n === "GO!" ? 650 : 800);
    }
    setCountdown("");
    const out = await act("/api/race/start");
    if (out) {
      setRaceOrder(out.state.race.lastResult.order || []);
      await wait(10500);
    }
    setRacing(false);
  }
  const ranking = useMemo(
    () => [...(state?.players || [])].sort((a, b) => b.credits - a.credits),
    [state?.players],
  );
  if (!token)
    return (
      <main className="join">
        <p className="eyebrow">LOCAL MULTIPLAYER</p>
        <h1>
          LOCAL
          <br />
          <span>ARCADE</span>
        </h1>
        <p>같은 네트워크에서 최대 6명이 즐기는 미니게임</p>
        <form onSubmit={join}>
          <input name="code" maxLength={6} placeholder="참여 코드" required />
          <input name="nickname" maxLength={12} placeholder="닉네임" required />
          <button>입장하기</button>
        </form>
        <small>가상 크레딧은 게임 점수이며 현금 가치가 없습니다.</small>
        {error && <Toast text={error} />}
      </main>
    );
  if (!state) return <main className="loading">ARCADE LOADING...</main>;
  const race = state.race,
    hang = state.hangman || {};
  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">LOCAL ARCADE</p>
          <h2>{state.me.nickname}님, 준비됐나요?</h2>
        </div>
        <div className="credit">
          <small>MY SCORE</small>
          <strong>{state.me.credits.toLocaleString()}</strong>
        </div>
      </header>
      <a
        className="promo-banner"
        href={PROMO_POSTS.banner}
        target="_blank"
        rel="noreferrer"
        aria-label="피자헛 슈즈참 이벤트 Instagram에서 보기"
      >
        <img src="/ads/image2.jpg" alt="피자헛 슈즈참으로 꾸민 신발" />
        <span className="promo-copy">
          <small>귀엽고 힙한 한정판 굿즈</small>
          <strong>피자헛 슈즈참 5종 출시!</strong>
          <span>피자 M/L 주문 시 랜덤 1종을 1,000원에</span>
        </span>
        <span className="promo-cta">EVENT<br/><b>자세히 보기 →</b></span>
      </a>
      {promoOpen && (
        <div className="promo-modal-backdrop" role="presentation">
          <section className="promo-modal" role="dialog" aria-modal="true" aria-labelledby="promo-title">
            <button
              className="promo-close"
              aria-label="광고 닫기"
              onClick={() => {
                setPromoOpen(false);
                sessionStorage.setItem("arcade-promo-closed", "1");
              }}
            >
              ×
            </button>
            <img className="promo-modal-image" src="/ads/image1.jpg" alt="피자헛 슈즈참 5종 출시 이벤트 안내" />
            <p className="promo-modal-label">PIZZA HUT EVENT</p>
            <h2 id="promo-title">귀엽고 힙한!<br/>피자헛 슈즈참 5종 출시</h2>
            <p>
              피자 M/L 사이즈 주문 시 슈즈참 5종 중 랜덤 1종을 1,000원에 만나보세요.<br/>
              <b>2026. 08. 04 ~ 08. 31</b>
            </p>
            <a href={PROMO_POSTS.modal} target="_blank" rel="noreferrer">
              이벤트 게시물 보기
            </a>
            <button
              className="promo-later"
              onClick={() => {
                setPromoOpen(false);
                sessionStorage.setItem("arcade-promo-closed", "1");
              }}
            >
              나중에 보기
            </button>
          </section>
        </div>
      )}
      <div className="shell">
        <div className="content">
          <nav>
            {[
              ["race", "🐌 레이싱"],
              ["hangman", "🔤 1:1 행맨"],
              ["yacht", "🎲 야추"],
              ["mafia", "🕵 마피아"],
              ["quiz", "🧠 위키 퀴즈"],
              ["rpg", "🎮 캐릭터 조작 테스트"],
            ].map((x) => (
              <button
                key={x[0]}
                className={tab === x[0] ? "active" : ""}
                onClick={() => changeTab(x[0])}
              >
                {x[1]}
              </button>
            ))}
          </nav>
          {tab === "race" && (
            <Game
              title="SNAIL GRAND PRIX"
              sub="다섯 귀족이 펼치는 예측 불가 달팽이 경주"
            >
              <div className="snail-picks">
                {SNAILS.map((s, i) => {
                  const n = i + 1;
                  return (
                    <button
                      key={s.name}
                      className={chosenSnail === n ? "selected" : ""}
                      disabled={race.entrants.includes(state.me.id)}
                      onClick={() => setChosenSnail(n)}
                    >
                      <em>{s.crest}</em>
                      <span className={`snail snail-${n}`}>🐌</span>
                      <b>{s.name}</b>
                      <small>{s.title}</small>
                    </button>
                  );
                })}
              </div>
              <div className="race-track">
                {SNAILS.map((s, i) => {
                  const n = i + 1,
                    rank = raceOrder.indexOf(n);
                  return (
                    <div className="lane" key={s.name}>
                      <span
                        className={
                          "racing-snail snail-" +
                          n +
                          " " +
                          (rank >= 0 ? "run" : "")
                        }
                        style={raceMotionStyle(n, race.lastResult, rank)}
                      >
                        🐌
                      </span>
                      <b>
                        {s.name}
                        <small>{s.title}</small>
                      </b>
                    </div>
                  );
                })}
                <i className="finish">FINISH</i>
                {countdown && <div className="countdown">{countdown}</div>}
              </div>
              <div className="race-bets">
                {race.entries.map((e) => (
                  <span key={e.playerId}>
                    {e.nickname} → <b>{SNAILS[e.snail - 1].name}</b> ·{" "}
                    {e.bet.toLocaleString()}
                  </span>
                ))}
              </div>
              {race.lastResult?.winnerSnail && !racing && (
                <>
                  <div className="podium">
                    {race.lastResult.order?.slice(0, 3).map((snail, index) => {
                      const s = SNAILS[snail - 1];
                      return (
                        <div className="podium-place" key={snail}>
                          <em>{["🥇", "🥈", "🥉"][index]}</em>
                          <b>{s.name}</b>
                          <small>
                            {s.title} · {index + 1}위
                          </small>
                        </div>
                      );
                    })}
                  </div>
                  <div className="race-result">
                    🏆 {SNAILS[race.lastResult.winnerSnail - 1].name} 우승 ·{" "}
                    {race.lastResult.multiplier}배{" "}
                    {race.lastResult.winners?.length
                      ? `· 적중: ${race.lastResult.winners.join(", ")}`
                      : "· 적중자 없음"}
                  </div>
                </>
              )}
              <BetPicker
                values={[100, 500, 1000, 2500, 5000]}
                value={raceBet}
                set={setRaceBet}
              />
              <div className="game-actions">
                <button
                  className="action"
                  disabled={racing || race.entrants.includes(state.me.id)}
                  onClick={() =>
                    act("/api/race/join", {
                      bet: raceBet,
                      snail: chosenSnail,
                      snailCount: 5,
                    })
                  }
                >
                  {SNAILS[chosenSnail - 1].name} 선택
                </button>
                <button
                  disabled={racing || race.entrants.length < 1}
                  onClick={startRace}
                >
                  START RACE
                </button>
              </div>
            </Game>
          )}
          {tab === "hangman" && (
            <Game
              title="1:1 HANGMAN DUEL"
              sub="정답을 맞힐 때마다 상대 행맨에 몸이 붙는다"
            >
              <div className="hang-duel">
                {[0, 1].map((i) => (
                  <div
                    className={
                      "fighter " +
                      (hang.players?.[i] === state.me.id ? "mine" : "")
                    }
                    key={i}
                  >
                    <h4>{hang.names?.[i] || "PLAYER"}</h4>
                    <HangmanDrawing wrong={hang.damage?.[i] || 0} />
                    <div className="damage">
                      DAMAGE {hang.damage?.[i] || 0} / 7
                    </div>
                  </div>
                ))}
                <div className="duel-center">
                  <span>ROUND {hang.round || 1}</span>
                  <div className="word">{hang.word || "_ _ _ _ _"}</div>
                  <p>{hang.message || "상대를 선택해 결투를 시작하세요."}</p>
                </div>
              </div>
              <div className="keyboard">
                {letters.map((l) => (
                  <button
                    key={l}
                    disabled={
                      !hang.word || hang.done || hang.guessed?.includes(l)
                    }
                    onClick={() => act("/api/hangman/guess", { letter: l })}
                  >
                    {l}
                  </button>
                ))}
              </div>
              {!hang.word && (
                <>
                  <div className="opponents">
                    {state.players
                      .filter((p) => p.id !== state.me.id)
                      .map((p) => (
                        <label key={p.id}>
                          <input type="radio" name="opponent" value={p.id} />
                          <span>{p.nickname}</span>
                        </label>
                      ))}
                  </div>
                  <BetPicker
                    values={[50, 100, 250]}
                    value={hangBet}
                    set={setHangBet}
                  />
                  <button
                    className="action"
                    onClick={() => {
                      const o = document.querySelector<HTMLInputElement>(
                        "[name=opponent]:checked",
                      );
                      o
                        ? act("/api/hangman/start", {
                            opponent: o.value,
                            stake: hangBet,
                          })
                        : fail(Error("상대를 선택하세요."));
                    }}
                  >
                    대결 신청
                  </button>
                </>
              )}
            </Game>
          )}
          {tab === "yacht" && social && (
            <YachtGameView
              me={state.me}
              yacht={social.yacht}
              categories={social.categories}
              held={held}
              setHeld={setHeld}
              bet={yachtBet}
              setBet={setYachtBet}
              rolling={yachtRolling}
              act={socialAct}
            />
          )}{" "}
          {tab === "mafia" && mafia && (
            <MafiaGameView me={state.me} mafia={mafia} act={mafiaAct} />
          )}
          {tab === "quiz" && <WikiQuiz api={api} refresh={refresh} fail={fail} />}
          {tab === "rpg" && <YuniRpg />}
        </div>
        <aside>
          <h3>LIVE RANKING</h3>
          {ranking.map((p, i) => (
            <div
              className={"rank " + (p.id === state.me.id ? "me" : "")}
              key={p.id}
            >
              <em>{i + 1}</em>
              <span>{p.nickname}</span>
              <strong>{p.credits.toLocaleString()}</strong>
            </div>
          ))}
          <div className="online-count">
            <i /> {state.players.length}/6 ONLINE
          </div>
          <ChatPanel
            messages={social?.chat || []}
            send={(text) => socialAct("/api/chat", { text })}
          />
        </aside>
      </div>
      <footer>로컬 게임용 가상 점수 · 결제 / 충전 / 환전 기능 없음</footer>
      {error && <Toast text={error} />}
    </main>
  );
}

function Game({
  title,
  sub,
  children,
}: {
  title: string;
  sub: string;
  children: React.ReactNode;
}) {
  return (
    <section className="game">
      <div className="game-title">
        <div>
          <p>{sub}</p>
          <h3>{title}</h3>
        </div>
        <span>● LIVE</span>
      </div>
      {children}
    </section>
  );
}

type QuizQuestion = {
  id: string;
  category: string;
  type: "concept" | "code_output" | "debugging" | "scenario" | "true_false";
  prompt: string;
  choices: string[];
  reward: number;
};
type QuizResult = {
  correct: boolean;
  correctChoice: number;
  explanation: string;
  source: string;
  reward: number;
};
const QUIZ_TYPE_LABEL: Record<QuizQuestion["type"], string> = {
  concept: "개념",
  code_output: "코드 결과",
  debugging: "오류 찾기",
  scenario: "상황 판단",
  true_false: "참 / 거짓",
};
function WikiQuiz({
  api,
  refresh,
  fail,
}: {
  api: (path: string, data?: unknown) => Promise<any>;
  refresh: () => Promise<void>;
  fail: (e: unknown) => void;
}) {
  const [question, setQuestion] = useState<QuizQuestion>();
  const [result, setResult] = useState<QuizResult>();
  const [selected, setSelected] = useState<number>();
  const [loading, setLoading] = useState(false);

  async function next() {
    setLoading(true);
    setResult(undefined);
    setSelected(undefined);
    try {
      setQuestion(await api("/api/quiz/next"));
    } catch (e) {
      fail(e);
    } finally {
      setLoading(false);
    }
  }
  async function submit() {
    if (!question || selected === undefined || result) return;
    setLoading(true);
    try {
      const out = await api("/api/quiz/answer", {
        questionId: question.id,
        choice: selected,
      });
      setResult(out);
      await refresh();
    } catch (e) {
      fail(e);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { next(); }, []);
  return (
    <Game title="LLM WIKI CHALLENGE" sub="내 학습 기록에서 Luna가 출제하는 프로그래밍 퀴즈">
      <div className="quiz-guide">
        <span>📚 Obsidian 없이 Markdown 위키를 직접 사용</span>
        <span>✨ 정답 +100 SCORE</span>
        <span>🔀 개념 · 코드 · 디버깅 · 상황형 혼합</span>
      </div>
      {loading && !question ? (
        <div className="quiz-loading">LUNA가 위키에서 문제를 만드는 중...</div>
      ) : question ? (
        <div className="quiz-card">
          <div className="quiz-meta">
            <b>{question.category}</b>
            <span>{QUIZ_TYPE_LABEL[question.type]}</span>
          </div>
          <h4>{question.prompt}</h4>
          <div className="quiz-choices">
            {question.choices.map((choice, index) => {
              const judged = result !== undefined;
              const cls = judged
                ? index === result.correctChoice
                  ? "correct"
                  : index === selected
                    ? "wrong"
                    : ""
                : selected === index ? "selected" : "";
              return (
                <button key={index} className={cls} disabled={judged || loading} onClick={() => setSelected(index)}>
                  <em>{String.fromCharCode(65 + index)}</em><span>{choice}</span>
                </button>
              );
            })}
          </div>
          {!result ? (
            <button className="action quiz-submit" disabled={selected === undefined || loading} onClick={submit}>
              {loading ? "채점 중..." : "정답 제출"}
            </button>
          ) : (
            <div className={`quiz-result ${result.correct ? "correct" : "wrong"}`}>
              <h3>{result.correct ? `정답! +${result.reward} SCORE` : "아쉽지만 오답!"}</h3>
              <p>{result.explanation}</p>
              <small>출처 · LlmWiki_Backup/{result.source}</small>
              <button className="action" onClick={next} disabled={loading}>{loading ? "생성 중..." : "다음 문제"}</button>
            </div>
          )}
        </div>
      ) : (
        <button className="action quiz-retry" onClick={next}>문제 다시 불러오기</button>
      )}
    </Game>
  );
}
function BetPicker({
  values,
  value,
  set,
}: {
  values: number[];
  value: number;
  set: (n: number) => void;
}) {
  return (
    <div className="bet-picker">
      <span>게임 점수</span>
      {values.map((n) => (
        <button
          key={n}
          className={value === n ? "selected" : ""}
          onClick={() => set(n)}
        >
          {n}
        </button>
      ))}
    </div>
  );
}
function HangmanDrawing({ wrong }: { wrong: number }) {
  return (
    <svg className="gallows" viewBox="0 0 180 190">
      <path d="M15 175h150M45 175V15h80M125 15v28" />
      {wrong > 0 && <circle cx="125" cy="58" r="15" />}
      {wrong > 1 && <path d="M125 73v48" />}
      {wrong > 2 && <path d="M125 83l-25 25" />}
      {wrong > 3 && <path d="M125 83l25 25" />}
      {wrong > 4 && <path d="M125 121l-23 35" />}
      {wrong > 5 && <path d="M125 121l23 35" />}
      {wrong > 6 && <path d="M118 55l5 5m0-5l-5 5m9-5l5 5m0-5l-5 5" />}
    </svg>
  );
}
function ChatPanel({
  messages,
  send,
}: {
  messages: ChatMessage[];
  send: (text: string) => void;
}) {
  const logRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    logRef.current?.scrollTo({
      top: logRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages.at(-1)?.id]);
  return (
    <section className="chat-panel">
      <div className="chat-toggle">
        💬 CHAT <span>{messages.length}</span>
      </div>
      <div className="chat-log" ref={logRef}>
        {messages.map((m) => (
          <p key={m.id}>
            <b>{m.nickname}</b> : {m.text}
          </p>
        ))}
        {!messages.length && <small>첫 메시지를 남겨보세요.</small>}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const f = new FormData(e.currentTarget),
            text = String(f.get("message") || "");
          if (text.trim()) {
            send(text);
            e.currentTarget.reset();
          }
        }}
      >
        <input name="message" maxLength={200} placeholder="메시지 입력" />
        <button>전송</button>
      </form>
    </section>
  );
}
type YuniAction = "idle" | "walk" | "run" | "jump";
function YuniRpg() {
  const worldRef = useRef<HTMLDivElement>(null),
    keys = useRef(new Set<string>());
  const [pose, setPose] = useState({
    x: 70,
    y: 0,
    vy: 0,
    facing: 1 as 1 | -1,
    action: "idle" as YuniAction,
    frame: 0,
    grounded: true,
  });
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
        if (
          [
            "ArrowLeft",
            "ArrowRight",
            "ArrowUp",
            "ShiftLeft",
            "ShiftRight",
          ].includes(e.code)
        )
          e.preventDefault();
        keys.current.add(e.code);
        if (e.code === "ArrowUp" && !e.repeat) {
          setPose((p) =>
            p.grounded
              ? { ...p, vy: 470, grounded: false, action: "jump", frame: 0 }
              : p,
          );
        }
      },
      up = (e: KeyboardEvent) => {
        keys.current.delete(e.code);
      };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    let last = performance.now(),
      raf = 0;
    const tick = (now: number) => {
      const dt = Math.min((now - last) / 1000, 0.034);
      last = now;
      setPose((p) => {
        const width = worldRef.current?.clientWidth || 900,
          left = keys.current.has("ArrowLeft"),
          right = keys.current.has("ArrowRight"),
          running =
            keys.current.has("ShiftLeft") || keys.current.has("ShiftRight");
        let { x, y, vy, facing, grounded } = p;
        const dir = (right ? 1 : 0) - (left ? 1 : 0);
        if (dir) facing = dir as 1 | -1;
        x += dir * (running ? 265 : 150) * dt;
        const previousY = y;
        if (!grounded) {
          vy -= 1050 * dt;
          y = Math.max(0, y + vy * dt);
          if (y === 0) {
            vy = 0;
            grounded = true;
          }
          if (vy <= 0) {
            const platforms = [
              { left: width * 0.24, right: width * 0.47, height: 92 },
              { left: width * 0.58, right: width * 0.82, height: 166 },
            ];
            for (const platform of platforms) {
              const center = x + 55;
              if (
                center >= platform.left &&
                center <= platform.right &&
                previousY >= platform.height &&
                y <= platform.height
              ) {
                y = platform.height;
                vy = 0;
                grounded = true;
                break;
              }
            }
          }
        }
        x = Math.max(0, Math.min(width - 115, x));
        let action: YuniAction = !grounded
            ? "jump"
            : left || right
              ? running
                ? "run"
                : "walk"
              : "idle";
        const counts: Record<YuniAction, number> = {
            idle: 6,
            walk: 6,
            run: 6,
            jump: 3,
          },
          speed: Record<YuniAction, number> = {
            idle: 260,
            walk: 115,
            run: 80,
            jump: 105,
          };
        return {
          x,
          y,
          vy,
          facing,
          grounded,
          action,
          frame: Math.floor(now / speed[action]) % counts[action],
        };
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
  }, []);
  return (
    <Game title="CHARACTER CONTROL TEST" sub="유니 캐릭터의 이동과 액션을 확인하는 테스트 공간">
      <div className="rpg-help">
        <span>
          <kbd>←</kbd>
          <kbd>→</kbd> 이동
        </span>
        <span>
          <kbd>SHIFT</kbd> 달리기
        </span>
        <span>
          <kbd>↑</kbd> 점프
        </span>
      </div>
      <div className="yuni-world" ref={worldRef}>
        <div className="world-moon">✦</div>
        <div className="platform platform-one" />
        <div className="platform platform-two" />
        <div
          className="yuni-character"
          style={{
            left: 0,
            bottom: 42,
            transform: `translate3d(${pose.x}px, ${-pose.y}px, 0) scaleX(${pose.facing})`,
          }}
        >
          <YuniSprite action={pose.action} frame={pose.frame} />
          <span className="yuni-shadow" />
        </div>
        <div className="world-ground" />
        <div className="action-indicator">
          <b>{pose.action.toUpperCase()}</b>
          <span>{pose.grounded ? "GROUND" : "AIR"}</span>
        </div>
      </div>
      <p className="rpg-note">
        현재는 이동과 전투 동작을 확인하는 1인용 테스트 스테이지입니다.
      </p>
    </Game>
  );
}
function YuniSprite({ action, frame }: { action: YuniAction; frame: number }) {
  return (
    <img
      className={`yuni-sprite ${action}`}
      src={`/yuni/${action}/${frame}.png`}
      alt=""
      draggable={false}
    />
  );
}
function MafiaGameView({
  me,
  mafia,
  act,
}: {
  me: Player;
  mafia: MafiaState;
  act: (p: string, d?: unknown) => Promise<unknown>;
}) {
  const [seconds, setSeconds] = useState(mafia.remainingSeconds || 0),
    [phaseIntro, setPhaseIntro] = useState<"DAY" | "NIGHT" | null>(null),
    phaseKey = useRef("");
  useEffect(() => {
    setSeconds(mafia.remainingSeconds || 0);
  }, [mafia.remainingSeconds, mafia.phase]);
  useEffect(() => {
    if (!mafia.active) return;
    const id = setInterval(() => setSeconds((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(id);
  }, [mafia.active, mafia.phase]);
  useEffect(() => {
    if (!mafia.active || (mafia.phase !== "DAY" && mafia.phase !== "NIGHT"))
      return;
    const key = `${mafia.round}-${mafia.phase}`;
    if (phaseKey.current === key) return;
    phaseKey.current = key;
    setPhaseIntro(mafia.phase);
    const id = setTimeout(() => setPhaseIntro(null), 2800);
    return () => clearTimeout(id);
  }, [mafia.active, mafia.phase, mafia.round]);
  const joined = mafia.lobby.some((x) => x.playerId === me.id),
    mine = mafia.lobby.find((x) => x.playerId === me.id),
    player = mafia.players?.find((x) => x.playerId === me.id),
    alive = player?.alive || false,
    role = mafia.myRole || "SPECTATOR",
    canAct =
      alive &&
      !mafia.acted &&
      (mafia.phase === "DAY" ||
        (mafia.phase === "NIGHT" && (role === "MAFIA" || role === "DOCTOR"))),
    roleName: { [key: string]: string } = {
      MAFIA: "마피아",
      DOCTOR: "의사",
      CITIZEN: "시민",
      SPECTATOR: "관전자",
    };
  const targets = (mafia.players || []).filter(
    (p) =>
      p.alive &&
      p.playerId !== me.id &&
      (mafia.phase !== "NIGHT" || role !== "MAFIA" || p.role !== "MAFIA"),
  );
  return (
    <Game
      title="MIDNIGHT MAFIA"
      sub="대화와 추리로 숨어 있는 마피아를 찾아내세요"
    >
      {phaseIntro && (
        <div className={`mafia-transition ${phaseIntro.toLowerCase()}`}>
          <em>{phaseIntro === "DAY" ? "☀️" : "🌙"}</em>
          <strong>
            {phaseIntro === "DAY" ? "낮이 되었습니다" : "밤이 되었습니다"}
          </strong>
          <span>
            {phaseIntro === "DAY"
              ? "대화하며 투표를 진행해 주세요."
              : "마피아와 의사는 죽일 사람과 살릴 사람을 선택하세요."}
          </span>
        </div>
      )}
      {!mafia.active && !mafia.done ? (
        <>
          <div className="mafia-rules">
            <span>4~5명 · 마피아 1 / 의사 1</span>
            <span>6명 · 마피아 2 / 의사 1</span>
            <b>전원이 READY하면 자동 시작</b>
          </div>
          <div className="mafia-lobby">
            {mafia.lobby.map((p, i) => (
              <div key={p.playerId}>
                <MafiaAvatar index={i} />
                <b>{p.nickname}</b>
                <span className={p.ready ? "ready" : ""}>
                  {p.ready ? "READY" : "WAITING"}
                </span>
              </div>
            ))}
            {!mafia.lobby.length && <p>아직 참가자가 없습니다.</p>}
          </div>
          <div className="game-actions">
            <button
              className="action"
              disabled={joined}
              onClick={() => act("/api/mafia/join")}
            >
              참여하기
            </button>
            <button
              disabled={!joined}
              className={mine?.ready ? "ready-on" : ""}
              onClick={() => act("/api/mafia/ready")}
            >
              {mine?.ready ? "READY 취소" : "READY"}
            </button>
          </div>
          <p className="mafia-minimum">
            최소 4명이 필요합니다 · 현재 {mafia.lobby.length}/6명
          </p>
        </>
      ) : (
        <>
          <div
            className={
              "mafia-phase " + (mafia.phase === "NIGHT" ? "night" : "day")
            }
          >
            <div>
              <small>ROUND {mafia.round}</small>
              <h2>{mafia.phase === "NIGHT" ? "🌙 밤" : "☀️ 낮"}</h2>
            </div>
            <strong>
              {String(Math.floor(seconds / 60)).padStart(2, "0")}:
              {String(seconds % 60).padStart(2, "0")}
            </strong>
            <span>{mafia.message}</span>
          </div>
          <div className={"role-card role-" + role.toLowerCase()}>
            <small>나의 역할</small>
            <b>{roleName[role]}</b>
            <span>
              {role === "MAFIA"
                ? "밤에 제거할 사람을 고르세요."
                : role === "DOCTOR"
                  ? "밤에 살릴 사람을 고르세요."
                  : role === "CITIZEN"
                    ? "낮의 대화와 투표로 마피아를 찾으세요."
                    : "게임을 관전하고 있습니다."}
            </span>
          </div>
          <div className="mafia-town">
            {(mafia.players || []).map((p, i) => (
              <button
                key={p.playerId}
                className={
                  (p.alive ? "" : "eliminated") +
                  (p.playerId === mafia.myVote || p.playerId === mafia.myTarget
                    ? " selected"
                    : "")
                }
                disabled={
                  !canAct || !targets.some((t) => t.playerId === p.playerId)
                }
                onClick={() => act("/api/mafia/act", { target: p.playerId })}
              >
                <MafiaAvatar index={i} />
                <b>{p.nickname}</b>
                <small>
                  {p.alive
                    ? p.role !== "HIDDEN"
                      ? roleName[p.role]
                      : "생존"
                    : "탈락"}
                </small>
              </button>
            ))}
          </div>
          {mafia.acted && mafia.active && (
            <p className="acted-notice">
              ✓ 선택 완료 · 다른 플레이어를 기다리는 중
            </p>
          )}
          <MafiaChat
            messages={mafia.chat || []}
            phase={mafia.phase}
            role={role}
            enabled={alive && !mafia.done}
            send={(text) => act("/api/mafia/chat", { text })}
          />
          {mafia.active && player && (
            <button
              className="cancel-game"
              onClick={() =>
                confirm("진행 중인 마피아 게임을 종료할까요?") &&
                act("/api/mafia/cancel")
              }
            >
              마피아 게임 종료
            </button>
          )}
          {mafia.done && (
            <div className="mafia-result">
              <h2>{mafia.message}</h2>
              <button className="action" onClick={() => act("/api/mafia/join")}>
                새 게임 참여
              </button>
            </div>
          )}
        </>
      )}
    </Game>
  );
}
function MafiaChat({
  messages,
  phase,
  role,
  enabled,
  send,
}: {
  messages: NonNullable<MafiaState["chat"]>;
  phase: MafiaState["phase"];
  role: string;
  enabled: boolean;
  send: (text: string) => Promise<unknown>;
}) {
  const logRef = useRef<HTMLDivElement>(null),
    [draft, setDraft] = useState(""),
    [sending, setSending] = useState(false),
    canChat = enabled && (phase !== "NIGHT" || role === "MAFIA");
  useEffect(() => {
    const log = logRef.current;
    if (log) log.scrollTop = log.scrollHeight;
  }, [messages.at(-1)?.id]);
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const text = draft.trim();
    if (!text || sending || !canChat) return;
    setSending(true);
    const result = await send(text);
    if (result) setDraft("");
    setSending(false);
  }
  return (
    <section className="mafia-only-chat">
      <header>
        <b>
          {phase === "NIGHT" && role === "MAFIA"
            ? "🔒 마피아 비밀 채팅"
            : "💬 마을 전용 채팅"}
        </b>
        <small>마피아 게임에서만 사용됩니다</small>
      </header>
      <div className="mafia-only-log" ref={logRef}>
        {messages.map((m) => (
          <p
            key={`mafia-${m.id}`}
            className={m.scope === "MAFIA" ? "secret" : ""}
          >
            <b>{m.nickname}</b>
            <span>{m.text}</span>
          </p>
        ))}
        {!messages.length && <small>아직 메시지가 없습니다.</small>}
      </div>
      <form onSubmit={submit}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          maxLength={200}
          disabled={!canChat || sending}
          placeholder={
            !canChat ? "지금은 채팅할 수 없습니다" : "마피아 게임 메시지 입력"
          }
        />
        <button disabled={!canChat || sending || !draft.trim()}>
          {sending ? "전송 중" : "전송"}
        </button>
      </form>
    </section>
  );
}
function MafiaAvatar({ index }: { index: number }) {
  return (
    <span className={"mafia-avatar avatar-" + (index % 6)}>
      <i />
      <em>{["🙂", "😎", "😊", "🤓", "😄", "🫡"][index % 6]}</em>
    </span>
  );
}
function YachtGameView({
  me,
  yacht,
  categories,
  held,
  setHeld,
  bet,
  setBet,
  rolling,
  act,
}: {
  me: Player;
  yacht: Yacht;
  categories: string[];
  held: boolean[];
  setHeld: (v: boolean[]) => void;
  bet: number;
  setBet: (n: number) => void;
  rolling: boolean;
  act: (p: string, d?: unknown) => Promise<unknown>;
}) {
  const effectKey = useRef("");
  const [diceSkin, setDiceSkin] = useState<"white" | "red">(() =>
    localStorage.getItem("yacht-dice-skin") === "red" ? "red" : "white",
  );
  function chooseDiceSkin(skin: "white" | "red") {
    setDiceSkin(skin);
    localStorage.setItem("yacht-dice-skin", skin);
  }
  const participant = yacht.players?.includes(me.id) || false,
    myTurn = !yacht.done && yacht.currentPlayer === me.id,
    joined = yacht.lobby.some((x) => x.playerId === me.id);
  const readySignature = yacht.lobby
      .map((x) => `${x.playerId}:${Boolean((x as { ready?: boolean }).ready)}`)
      .join("|"),
    myReady = Boolean(
      (
        yacht.lobby.find((x) => x.playerId === me.id) as
          | { ready?: boolean }
          | undefined
      )?.ready,
    );
  useEffect(() => {
    if (yacht.active) return;
    const lobby = document.querySelector(".yacht-lobby");
    lobby?.querySelectorAll("span").forEach((node, i) => {
      const item = yacht.lobby[i] as {
        nickname: string;
        stake: number;
        ready?: boolean;
      };
      node.textContent = `${item.nickname} · ${item.stake} · ${item.ready ? "READY" : "WAITING"}`;
      node.classList.toggle("ready", Boolean(item.ready));
    });
    const button = lobby?.parentElement?.querySelector<HTMLButtonElement>(
      ".game-actions button:last-child",
    );
    if (button) button.textContent = myReady ? "READY 취소" : "READY";
  }, [readySignature, yacht.active, myReady]);
  const meta: Record<string, [string, string, string]> = {
    ACES: ["에이스", "1이 나온 주사위 합", "1·1·4·5·6 → 2점"],
    DEUCES: ["듀스", "2가 나온 주사위 합", "2·2·3·5·6 → 4점"],
    THREES: ["트레이", "3이 나온 주사위 합", "3·3·3·5·6 → 9점"],
    FOURS: ["포", "4가 나온 주사위 합", "4·4·2·3·6 → 8점"],
    FIVES: ["파이브", "5가 나온 주사위 합", "5·5·5·2·3 → 15점"],
    SIXES: ["식스", "6이 나온 주사위 합", "6·6·1·3·4 → 12점"],
    CHOICE: ["초이스", "주사위 5개의 전체 합", "6·6·5·4·3 → 24점"],
    FOUR_KIND: ["포커", "같은 숫자 4개 이상이면 전체 합", "4·4·4·4·2 → 18점"],
    FULL_HOUSE: ["풀하우스", "같은 숫자 3개와 2개", "2·2·5·5·5 → 19점"],
    SMALL_STRAIGHT: ["스몰 스트레이트", "연속 숫자 4개", "1·2·3·4·6 → 15점"],
    LARGE_STRAIGHT: ["라지 스트레이트", "연속 숫자 5개", "2·3·4·5·6 → 30점"],
    YACHT: ["야추", "주사위 5개가 모두 같음", "6·6·6·6·6 → 50점"],
  };
  const myScores = yacht.scores?.[me.id] || {},
    dice = yacht.dice || [0, 0, 0, 0, 0],
    upperTotal = ["ACES", "DEUCES", "THREES", "FOURS", "FIVES", "SIXES"].reduce(
      (sum, c) => sum + (myScores[c] || 0),
      0,
    ),
    standings = (yacht.players || [])
      .map((id, i) => ({
        id,
        name: yacht.names?.[i],
        score:
          Object.values(yacht.scores?.[id] || {}).reduce((a, b) => a + b, 0) +
          (yacht.upperBonuses?.[id] || 0),
      }))
      .sort((a, b) => b.score - a.score);
  useEffect(() => {
    const key = `${yacht.currentPlayer}-${yacht.rolls}-${dice.join("")}`;
    if (
      dice[0] > 0 &&
      dice.every((n) => n === dice[0]) &&
      key !== effectKey.current
    ) {
      effectKey.current = key;
      document.body.classList.add("yacht-celebrating");
      const id = setTimeout(
        () => document.body.classList.remove("yacht-celebrating"),
        2400,
      );
      return () => {
        clearTimeout(id);
        document.body.classList.remove("yacht-celebrating");
      };
    }
  }, [dice.join(","), yacht.rolls, yacht.currentPlayer]);
  useEffect(() => {
    const sheet = document.querySelector<HTMLElement>(".score-sheet.detailed");
    if (sheet)
      sheet.dataset.upper = `숙제 ${upperTotal}/63 · ${upperTotal >= 63 ? "보너스 +35점 획득" : "63점 달성 시 +35점"}`;
  }, [upperTotal, yacht.active]);
  return (
    <Game title="YACHT DICE" sub="2~6명이 펼치는 5주사위 점수 대결">
      {!yacht.active ? (
        <>
          <div className="yacht-guide">
            <b>처음이라면 이렇게 하세요</b>
            <span>① 1차 굴리기</span>
            <span>② 남길 주사위 KEEP</span>
            <span>③ 2차 굴리기</span>
            <span>④ 다시 KEEP</span>
            <span>⑤ 3차 굴리기</span>
            <span>⑥ 점수 칸 선택</span>
          </div>
          <div className="yacht-lobby">
            <h3>참가자 {yacht.lobby.length}/6</h3>
            {yacht.lobby.map((x) => (
              <span key={x.playerId}>
                {x.nickname} · {x.stake}
              </span>
            ))}
          </div>
          <BetPicker values={[100, 500, 1000]} value={bet} set={setBet} />
          <div className="game-actions">
            <button
              className="action"
              disabled={joined}
              onClick={() => act("/api/yacht/join", { bet })}
            >
              참여하기
            </button>
            <button
              disabled={!joined || yacht.lobby.length < 2}
              onClick={() => act("/api/yacht/start")}
            >
              게임 시작
            </button>
          </div>
        </>
      ) : yacht.done ? (
        <div className="yacht-finished">
          <span>GAME FINISHED</span>
          <h2>{yacht.message}</h2>
          <div className="final-standing">
            {standings.map((p, i) => (
              <div key={p.id}>
                <em>{["🥇", "🥈", "🥉"][i] || `${i + 1}위`}</em>
                <b>{p.name}</b>
                <strong>{p.score}점</strong>
              </div>
            ))}
          </div>
          <BetPicker values={[100, 500, 1000]} value={bet} set={setBet} />
          <button
            className="action"
            onClick={() => act("/api/yacht/restart", { bet })}
          >
            {participant ? "다시 하기" : "참여하기"}
          </button>
        </div>
      ) : (
        <>
          <div className="playing-banner">
            <b>● 게임 진행 중</b>
            <span>
              {participant
                ? myTurn
                  ? "내 턴입니다"
                  : "다른 플레이어의 턴"
                : "관전 중 · 진행 중인 게임에는 참여할 수 없습니다"}
            </span>
          </div>
          <div className="yacht-status">
            <b>{yacht.message}</b>
            <span>게임 점수 {yacht.pot?.toLocaleString()}</span>
          </div>
          <div className="turn-help">
            {!participant
              ? "참가자들의 주사위와 점수표를 관전하고 있습니다."
              : !yacht.rolls
                ? "1차로 다섯 주사위를 굴리세요."
                : yacht.rolls === 1
                  ? "KEEP할 주사위를 고르고 2차로 굴리세요."
                  : yacht.rolls === 2
                    ? "KEEP을 다시 고르고 마지막 3차로 굴리거나 기록하세요."
                    : "세 번 모두 굴렸습니다. 점수 칸을 선택하세요."}
          </div>
          <div className="dice-skin-picker" aria-label="주사위 스킨 선택">
            <span>주사위 스킨</span>
            <button
              className={diceSkin === "white" ? "selected" : ""}
              onClick={() => chooseDiceSkin("white")}
            >
              <DiceSprite value={1} skin="white" /> 흰색
            </button>
            <button
              className={diceSkin === "red" ? "selected" : ""}
              onClick={() => chooseDiceSkin("red")}
            >
              <DiceSprite value={1} skin="red" /> 빨간색
            </button>
          </div>
          <div className={`dice-board dice-tray ${diceSkin}`}>
            <div className="tray-label">
              <span>YACHT THROW TRAY</span>
              <small>KEEP하지 않은 주사위만 다시 던져집니다</small>
            </div>
            {dice.map((d, i) => (
              <button
                key={i}
                className={held[i] ? "held" : ""}
                disabled={rolling || !myTurn || !d || yacht.rolls === 3}
                onClick={() => setHeld(held.map((x, j) => (j === i ? !x : x)))}
              >
                <DiceSprite value={d} skin={diceSkin} />
                <small>
                  {held[i] ? "KEEP" : "DICE"} <b>{d || "?"}</b>
                </small>
              </button>
            ))}
          </div>
          <button
            className="roll-button"
            disabled={rolling || !myTurn || yacht.rolls === 3}
            onClick={() => act("/api/yacht/roll", { held })}
          >
            {rolling ? "🎲 던지는 중..." : `🎲 ROLL ${yacht.rolls || 0}/3`}
          </button>
          <p className="score-hint">
            현재 조합을 기록할 칸을 선택하세요. 예상 점수가 표시됩니다.
          </p>
          <div className="score-sheet detailed">
            {categories.map((c) => {
              const m = meta[c],
                preview = yachtScore(c, dice);
              return (
                <button
                  key={c}
                  disabled={
                    rolling ||
                    !myTurn ||
                    !yacht.rolls ||
                    myScores[c] !== undefined
                  }
                  onClick={async () => {
                    await act("/api/yacht/score", {
                      category: c,
                      dice: [...dice],
                    });
                    setHeld([false, false, false, false, false]);
                  }}
                >
                  <span>
                    <strong>{m[0]}</strong>
                    <small>
                      {m[1]}
                      <i>{m[2]}</i>
                    </small>
                  </span>
                  <b>
                    {myScores[c] !== undefined
                      ? `${myScores[c]}점`
                      : `예상 ${preview}점`}
                  </b>
                </button>
              );
            })}
          </div>
          <div className="yacht-ranking">
            {standings.map((p) => (
              <span
                key={p.id}
                className={p.id === yacht.currentPlayer ? "turn" : ""}
              >
                {p.name} <b>{p.score}</b>
              </span>
            ))}
          </div>
          {participant && (
            <button
              className="cancel-game"
              disabled={rolling}
              onClick={() =>
                confirm("야추 게임을 종료하고 참가 점수를 모두 환불할까요?") &&
                act("/api/yacht/cancel")
              }
            >
              야추 게임 종료
            </button>
          )}
        </>
      )}
    </Game>
  );
}
function DiceSprite({ value, skin }: { value: number; skin: "white" | "red" }) {
  const x = [5.4, 25.7, 44.2, 62.4, 79.5, 97.45][Math.max(0, value - 1)];
  return value ? (
    <span
      className={`dice-sprite ${skin}`}
      style={{ backgroundPosition: `${x}% ${skin === "red" ? 74 : 15.3}%` }}
      role="img"
      aria-label={`${skin === "red" ? "빨간" : "흰"} 주사위 ${value}`}
    />
  ) : (
    <span className="dice-sprite empty">?</span>
  );
}
function yachtScore(c: string, d: number[]) {
  const count = Array(7).fill(0);
  d.forEach((n) => count[n]++);
  const sum = d.reduce((a, b) => a + b, 0),
    straight = (len: number) => {
      let run = 0;
      for (let i = 1; i <= 6; i++) {
        run = count[i] ? run + 1 : 0;
        if (run >= len) return true;
      }
      return false;
    };
  const upper: Record<string, number> = {
    ACES: 1,
    DEUCES: 2,
    THREES: 3,
    FOURS: 4,
    FIVES: 5,
    SIXES: 6,
  };
  if (upper[c]) return count[upper[c]] * upper[c];
  if (c === "CHOICE") return sum;
  if (c === "FOUR_KIND") return Math.max(...count) >= 4 ? sum : 0;
  if (c === "FULL_HOUSE")
    return (count.includes(3) && count.includes(2)) || count.includes(5)
      ? sum
      : 0;
  if (c === "SMALL_STRAIGHT") return straight(4) ? 15 : 0;
  if (c === "LARGE_STRAIGHT") return straight(5) ? 30 : 0;
  if (c === "YACHT") return count.includes(5) ? 50 : 0;
  return 0;
}
function Toast({ text }: { text: string }) {
  return <div className="toast">⚠ {text}</div>;
}
function AdminPage() {
  const [code, setCode] = useState(sessionStorage.getItem("admin-code") || ""),
    [players, setPlayers] = useState<Player[]>([]),
    [quizAdmin, setQuizAdmin] = useState<{generationEnabled:boolean;savedQuestions:number;model:string}>(),
    [error, setError] = useState("");
  async function call(path: string, data?: unknown) {
    const r = await fetch(API + path, {
      method: data ? "POST" : "GET",
      headers: { "Content-Type": "application/json", "X-Admin-Code": code },
      body: data ? JSON.stringify(data) : undefined,
    });
    const out = await r.json();
    if (!r.ok) throw Error(out.error || "관리자 요청 실패");
    if (Array.isArray(out.players)) setPlayers(out.players);
    return out;
  }
  async function load() {
    try {
      await call("/api/admin/players");
      setQuizAdmin(await call("/api/admin/quiz"));
      sessionStorage.setItem("admin-code", code);
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    if (!code) return;
    load();
    const id = setInterval(load, 2000);
    return () => clearInterval(id);
  }, [code]);
  return (
    <main className="admin">
      <header>
        <div>
          <p className="eyebrow">LOCAL ARCADE CONTROL</p>
          <h1>ADMIN PANEL</h1>
        </div>
        <a href="/">게임 화면</a>
      </header>
      {!players.length && (
        <section className="admin-login">
          <h2>관리자 인증</h2>
          <p>백엔드 콘솔에 표시된 관리자 코드를 입력하세요.</p>
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            placeholder="ADMIN CODE"
          />
          <button onClick={load}>접속</button>
          {error && <p className="admin-error">{error}</p>}
        </section>
      )}
      <section className="admin-grid">
        {players.map((p) => (
          <article key={p.id}>
            <div>
              <span>ONLINE PLAYER</span>
              <h2>{p.nickname}</h2>
              <strong>{p.credits.toLocaleString()} CR</strong>
            </div>
            <div className="admin-actions">
              {[1000, 5000, 10000].map((n) => (
                <button
                  className="grant"
                  onClick={() =>
                    call("/api/admin/grant", { playerId: p.id, amount: n })
                  }
                >
                  +{n.toLocaleString()}
                </button>
              ))}
              {[-1000, -5000, -10000].map((n) => (
                <button
                  className="deduct"
                  onClick={() =>
                    call("/api/admin/grant", { playerId: p.id, amount: n })
                  }
                >
                  {n.toLocaleString()}
                </button>
              ))}
              <button
                className="kick"
                onClick={() =>
                  confirm(`${p.nickname}님을 퇴출할까요?`) &&
                  call("/api/admin/kick", { playerId: p.id })
                }
              >
                퇴출
              </button>
            </div>
          </article>
        ))}
      </section>
      {quizAdmin && (
        <section className={`quiz-admin ${quizAdmin.generationEnabled ? "enabled" : "disabled"}`}>
          <div>
            <span>AI QUIZ CONTROL</span>
            <h2>위키 퀴즈 신규 출제</h2>
            <p>{quizAdmin.generationEnabled ? "Luna가 새 문제를 생성하고 DB에 저장합니다." : "API 호출 없이 저장된 문제만 무작위로 출제합니다."}</p>
          </div>
          <div className="quiz-admin-status">
            <small>{quizAdmin.model}</small>
            <strong>{quizAdmin.savedQuestions.toLocaleString()}개 저장됨</strong>
            <button onClick={async () => {
              try { setQuizAdmin(await call("/api/admin/quiz/toggle", { enabled: !quizAdmin.generationEnabled })); }
              catch (e) { setError((e as Error).message); }
            }}>
              {quizAdmin.generationEnabled ? "신규 출제 비활성화" : "신규 출제 활성화"}
            </button>
          </div>
        </section>
      )}
      {code && players.length === 0 && !error && (
        <div className="empty-admin">현재 접속자가 없습니다.</div>
      )}
    </main>
  );
}
function raceMotionStyle(
  snail: number,
  result: Race["lastResult"],
  rank: number,
) {
  let seed = ((result?.raceId || 1) + snail * 2654435761) >>> 0;
  const rnd = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };
  const points = [
    8 + rnd() * 15,
    20 + rnd() * 20,
    35 + rnd() * 22,
    51 + rnd() * 23,
    69 + rnd() * 20,
  ].map((n) => `${n.toFixed(1)}%`);
  return {
    "--p1": points[0],
    "--p2": points[1],
    "--p3": points[2],
    "--p4": points[3],
    "--p5": points[4],
    "--duration": `${(6.5 + Math.max(rank, 0) * 0.65 + rnd() * 0.35).toFixed(2)}s`,
  } as React.CSSProperties;
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
