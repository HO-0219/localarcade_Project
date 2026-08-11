package com.localarcade.game;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.localarcade.player.Player;
import com.localarcade.player.PlayerRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.SecureRandom;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Stream;

@Service
public class QuizGameService {
    private static final long REWARD = 100;
    private static final int HISTORY_LIMIT = 20;
    private static final int EXCERPT_LIMIT = 5_000;
    private final PlayerRepository players;
    private final QuizQuestionRepository questionRepo;
    private final QuizConfigRepository configRepo;
    private final ObjectMapper json;
    private final RestClient openai;
    private final String model;
    private final Path wikiRoot;
    private final SecureRandom random = new SecureRandom();
    private final Map<String, ActiveQuestion> active = new ConcurrentHashMap<>();
    private final Map<String, Deque<String>> histories = new ConcurrentHashMap<>();

    public QuizGameService(PlayerRepository players, QuizQuestionRepository questionRepo, QuizConfigRepository configRepo, ObjectMapper json,
                           @Value("${openai.api-key:}") String apiKey,
                           @Value("${openai.model:gpt-5.6-luna}") String model,
                           @Value("${quiz.wiki-root:../LlmWiki_Backup/wiki}") String wikiRoot) {
        this.players = players;
        this.questionRepo = questionRepo;
        this.configRepo = configRepo;
        this.json = json;
        this.model = model;
        this.wikiRoot = resolveWikiRoot(wikiRoot);
        this.openai = RestClient.builder().baseUrl("https://api.openai.com/v1")
            .defaultHeader("Authorization", "Bearer " + apiKey).build();
    }

    private Path resolveWikiRoot(String configured) {
        List<Path> candidates = List.of(Path.of(configured), Path.of("LlmWiki_Backup/wiki"), Path.of("../LlmWiki_Backup/wiki"));
        return candidates.stream().map(p -> p.toAbsolutePath().normalize()).filter(Files::isDirectory)
            .findFirst().orElse(candidates.getFirst().toAbsolutePath().normalize());
    }

    public Map<String, Object> next(Player player) {
        if (!Files.isDirectory(wikiRoot)) throw new IllegalStateException("퀴즈 위키 경로를 찾을 수 없습니다: " + wikiRoot);
        if (!generationEnabled()) return nextSaved(player);
        RuntimeException last = null;
        for (int attempt = 0; attempt < 3; attempt++) {
            try {
                GeneratedQuestion q = generate(player, attempt);
                String signature = normalize(q.prompt());
                Deque<String> history = histories.computeIfAbsent(player.getId(), ignored -> new ArrayDeque<>());
                if (history.stream().map(this::normalize).anyMatch(signature::equals)) continue;
                synchronized (history) {
                    history.addFirst(q.prompt());
                    while (history.size() > HISTORY_LIMIT) history.removeLast();
                }
                saveQuestion(q, signature);
                ActiveQuestion current = new ActiveQuestion(UUID.randomUUID().toString(), q);
                active.put(player.getId(), current);
                return view(current);
            } catch (RuntimeException e) { last = e; }
        }
        throw new IllegalStateException("새 문제를 만들지 못했습니다. 잠시 후 다시 시도해 주세요.", last);
    }

    private Map<String,Object> nextSaved(Player player) {
        List<QuizQuestionEntity> saved = questionRepo.findAll();
        if (saved.isEmpty()) throw new IllegalStateException("저장된 문제가 없습니다. 관리자가 AI 신규 출제를 잠시 활성화해야 합니다.");
        Deque<String> history = histories.computeIfAbsent(player.getId(), ignored -> new ArrayDeque<>());
        List<QuizQuestionEntity> fresh = saved.stream().filter(q -> history.stream().noneMatch(h -> normalize(h).equals(q.getSignature()))).toList();
        List<QuizQuestionEntity> pool = fresh.isEmpty() ? saved : fresh;
        QuizQuestionEntity entity = pool.get(random.nextInt(pool.size()));
        GeneratedQuestion q = new GeneratedQuestion(entity.getCategory(),entity.getQuestionType(),entity.getPrompt(),entity.getChoices(),entity.getAnswerIndex(),entity.getExplanation(),entity.getSource());
        synchronized(history){history.addFirst(q.prompt());while(history.size()>HISTORY_LIMIT)history.removeLast();}
        ActiveQuestion current = new ActiveQuestion(UUID.randomUUID().toString(),q);
        active.put(player.getId(),current);
        return view(current);
    }

    private void saveQuestion(GeneratedQuestion q, String signature) {
        if (questionRepo.findBySignature(signature).isEmpty()) questionRepo.save(new QuizQuestionEntity(q.category(),q.type(),signature,q.prompt(),q.choices(),q.answer(),q.explanation(),q.source()));
    }

    private boolean generationEnabled(){return configRepo.findById(1).orElseGet(()->configRepo.save(new QuizConfig(true))).isGenerationEnabled();}

    @Transactional public Map<String,Object> adminStatus(){return Map.of("generationEnabled",generationEnabled(),"savedQuestions",questionRepo.count(),"model",model);}
    @Transactional public Map<String,Object> setGenerationEnabled(boolean enabled){QuizConfig config=configRepo.findById(1).orElseGet(()->new QuizConfig(enabled));config.setGenerationEnabled(enabled);configRepo.save(config);return adminStatus();}

    private GeneratedQuestion generate(Player player, int attempt) {
        List<WikiExcerpt> excerpts = pickExcerpts(3);
        Deque<String> history = histories.getOrDefault(player.getId(), new ArrayDeque<>());
        String previous = history.isEmpty() ? "없음" : String.join("\n- ", history);
        StringBuilder materials = new StringBuilder();
        excerpts.forEach(e -> materials.append("\n\n[SOURCE: ").append(e.source()).append("]\n").append(e.text()));
        String prompt = """
            아래 LLM Wiki 발췌문만 근거로 한국어 프로그래밍 퀴즈 한 문제를 만들어라.
            학습자는 풀스택 개발 입문~중급 수준이다. 사실이 애매하거나 발췌문으로 검증할 수 없는 내용은 묻지 마라.
            유형은 concept, code_output, debugging, scenario, true_false 중 하나를 맥락에 맞게 고른다.
            code_output은 발췌문에서 확실히 검증 가능한 짧은 코드만 사용한다. true_false도 선택지는 정확히 2개다.
            나머지 유형은 선택지 4개를 만들고 오답도 그럴듯하되 명백히 틀려야 한다.
            정답 위치는 무작위로 정하고, explanation은 정답 이유와 대표 오답의 함정을 2~3문장으로 설명한다.
            source는 반드시 제공된 SOURCE 경로 중 하나를 그대로 사용한다. 최근 문제와 같은 핵심 개념이나 표현을 피한다.

            최근 출제 문제:
            - %s

            위키 발췌문:
            %s
            """.formatted(previous, materials);

        Map<String, Object> schema = Map.of(
            "type", "object", "additionalProperties", false,
            "properties", Map.of(
                "category", Map.of("type", "string"),
                "type", Map.of("type", "string", "enum", List.of("concept", "code_output", "debugging", "scenario", "true_false")),
                "prompt", Map.of("type", "string"),
                "choices", Map.of("type", "array", "items", Map.of("type", "string"), "minItems", 2, "maxItems", 4),
                "answer", Map.of("type", "integer", "minimum", 0, "maximum", 3),
                "explanation", Map.of("type", "string"),
                "source", Map.of("type", "string")),
            "required", List.of("category", "type", "prompt", "choices", "answer", "explanation", "source"));
        Map<String, Object> body = Map.of(
            "model", model,
            "input", prompt,
            "reasoning", Map.of("effort", "low"),
            "max_output_tokens", 900,
            "text", Map.of("verbosity", "low", "format", Map.of("type", "json_schema", "name", "wiki_quiz", "strict", true, "schema", schema)));
        JsonNode response = openai.post().uri("/responses").contentType(MediaType.APPLICATION_JSON)
            .body(body).retrieve().body(JsonNode.class);
        String output = extractOutputText(response);
        try {
            GeneratedQuestion q = json.readValue(output, GeneratedQuestion.class);
            validate(q, excerpts);
            return q;
        } catch (Exception e) { throw new IllegalStateException("생성된 문제 형식이 올바르지 않습니다.", e); }
    }

    private List<WikiExcerpt> pickExcerpts(int count) {
        try (Stream<Path> paths = Files.walk(wikiRoot)) {
            List<Path> candidates = paths.filter(Files::isRegularFile).filter(p -> p.toString().endsWith(".md"))
                .filter(p -> !p.toString().contains(FileSystems.getDefault().getSeparator() + "_meta" + FileSystems.getDefault().getSeparator()))
                .filter(p -> !p.getFileName().toString().equals("index.md") && !p.getFileName().toString().equals("log.md"))
                .toList();
            if (candidates.isEmpty()) throw new IllegalStateException("출제할 위키 문서가 없습니다.");
            List<Path> shuffled = new ArrayList<>(candidates);
            Collections.shuffle(shuffled, random);
            List<WikiExcerpt> result = new ArrayList<>();
            for (Path p : shuffled.subList(0, Math.min(count, shuffled.size()))) {
                String text = Files.readString(p, StandardCharsets.UTF_8)
                    .replaceAll("(?s)^---.*?---\\s*", "")
                    .replaceAll("!\\[\\[[^]]+]]", "[이미지 생략]");
                if (text.length() > EXCERPT_LIMIT) text = text.substring(0, EXCERPT_LIMIT);
                result.add(new WikiExcerpt("wiki/" + wikiRoot.relativize(p).toString().replace('\\', '/'), text));
            }
            return result;
        } catch (Exception e) { throw new IllegalStateException("위키 문서를 읽지 못했습니다.", e); }
    }

    private String extractOutputText(JsonNode response) {
        if (response == null) throw new IllegalStateException("OpenAI 응답이 비어 있습니다.");
        if (response.hasNonNull("output_text")) return response.get("output_text").asText();
        for (JsonNode item : response.path("output")) for (JsonNode content : item.path("content"))
            if ("output_text".equals(content.path("type").asText())) return content.path("text").asText();
        throw new IllegalStateException("OpenAI 응답에서 문제를 찾지 못했습니다.");
    }

    private void validate(GeneratedQuestion q, List<WikiExcerpt> excerpts) {
        if (q == null || q.prompt() == null || q.prompt().isBlank() || q.choices() == null || q.explanation() == null)
            throw new IllegalArgumentException("필수 문제 정보가 없습니다.");
        if (q.choices().size() < 2 || q.choices().size() > 4 || q.answer() < 0 || q.answer() >= q.choices().size())
            throw new IllegalArgumentException("선택지 또는 정답 번호가 올바르지 않습니다.");
        if (excerpts.stream().noneMatch(e -> e.source().equals(q.source())))
            throw new IllegalArgumentException("출처가 제공된 위키 문서와 일치하지 않습니다.");
    }

    @Transactional
    public Map<String, Object> answer(Player player, String questionId, int choice) {
        ActiveQuestion current = active.remove(player.getId());
        if (current == null || !current.id().equals(questionId)) throw new IllegalArgumentException("문제가 만료되었습니다. 새 문제를 받아 주세요.");
        GeneratedQuestion q = current.question();
        if (choice < 0 || choice >= q.choices().size()) throw new IllegalArgumentException("답을 선택해 주세요.");
        boolean correct = choice == q.answer();
        if (correct) { player.credit(REWARD); players.save(player); }
        return Map.of("correct", correct, "correctChoice", q.answer(), "explanation", q.explanation(), "source", q.source(), "reward", correct ? REWARD : 0);
    }

    private Map<String, Object> view(ActiveQuestion current) {
        GeneratedQuestion q = current.question();
        return Map.of("id", current.id(), "category", q.category(), "type", q.type(), "prompt", q.prompt(), "choices", q.choices(), "reward", REWARD);
    }

    private String normalize(String text) { return text.toLowerCase(Locale.ROOT).replaceAll("[^가-힣a-z0-9]", ""); }
    private record WikiExcerpt(String source, String text) {}
    private record GeneratedQuestion(String category, String type, String prompt, List<String> choices, int answer, String explanation, String source) {}
    private record ActiveQuestion(String id, GeneratedQuestion question) {}
}
