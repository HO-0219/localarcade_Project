package com.localarcade.game;

import com.localarcade.player.Player;
import com.localarcade.config.GameCommandQueue;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController @RequestMapping("/api")
public class GameController {
    private final GameService service; private final SocialGameService social; private final MafiaGameService mafia; private final QuizGameService quiz; private final GameCommandQueue queue;
    public GameController(GameService service,SocialGameService social,MafiaGameService mafia,QuizGameService quiz,GameCommandQueue queue){this.service=service;this.social=social;this.mafia=mafia;this.quiz=quiz;this.queue=queue;}
    private Player player(String auth){return service.auth(auth==null?"":auth.replaceFirst("^Bearer ",""));}
    @PostMapping("/join") Map<String,String> join(@RequestBody Join r){return queue.run(()->Map.of("token",service.join(r.code,r.nickname)));}
    @GetMapping("/state") Object state(@RequestHeader(value="Authorization",required=false)String a){Player p=player(a);return service.state(p);}
    @PostMapping("/race/{action}") Object race(@RequestHeader("Authorization")String a,@PathVariable String action,@RequestBody(required=false)RaceBet r){return queue.run(()->Map.of("state",service.race(player(a),action,r==null?0:r.bet,r==null?0:r.snail,r==null?0:r.snailCount)));}
    @PostMapping("/hangman/start") Object hangman(@RequestHeader("Authorization")String a,@RequestBody HangmanStart r){return queue.run(()->Map.of("state",service.startHangman(player(a),r.opponent,r.stake)));}
    @PostMapping("/hangman/guess") Object guess(@RequestHeader("Authorization")String a,@RequestBody Guess r){return queue.run(()->Map.of("state",service.guess(player(a),r.letter)));}
    @PostMapping("/game/leave") Object leave(@RequestHeader("Authorization")String a,@RequestBody Leave r){return queue.run(()->Map.of("state",service.leave(player(a),r.game)));}
    @GetMapping("/quiz/next") Object quizNext(@RequestHeader("Authorization")String a){return quiz.next(player(a));}
    @PostMapping("/quiz/answer") Object quizAnswer(@RequestHeader("Authorization")String a,@RequestBody QuizAnswer r){return queue.run(()->quiz.answer(player(a),r.questionId,r.choice));}
    @GetMapping("/social/state") Object socialState(@RequestHeader("Authorization")String a){return social.state(player(a));}
    @PostMapping("/chat") Object chat(@RequestHeader("Authorization")String a,@RequestBody Chat r){return queue.run(()->social.chat(player(a),r.text));}
    @PostMapping("/yacht/join") Object yachtJoin(@RequestHeader("Authorization")String a,@RequestBody Bet r){return queue.run(()->social.joinYacht(player(a),r.bet));}
    @PostMapping("/yacht/ready") Object yachtReady(@RequestHeader("Authorization")String a){return queue.run(()->social.readyYacht(player(a)));}
    @PostMapping("/yacht/start") Object yachtStart(@RequestHeader("Authorization")String a){return queue.run(()->social.readyYacht(player(a)));}
    @PostMapping("/yacht/restart") Object yachtRestart(@RequestHeader("Authorization")String a,@RequestBody Bet r){return queue.run(()->social.restartYacht(player(a),r.bet));}
    @PostMapping("/yacht/roll") Object yachtRoll(@RequestHeader("Authorization")String a,@RequestBody YachtRoll r){return queue.run(()->social.roll(player(a),r.held));}
    @PostMapping("/yacht/score") Object yachtScore(@RequestHeader("Authorization")String a,@RequestBody YachtScore r){return queue.run(()->social.score(player(a),r.category,r.dice));}
    @PostMapping("/yacht/cancel") Object yachtCancel(@RequestHeader("Authorization")String a){return queue.run(()->social.cancelYacht(player(a)));}
    @PostMapping("/yacht/leave") Object yachtLeave(@RequestHeader("Authorization")String a){return queue.run(()->social.leave(player(a)));}
    @GetMapping("/mafia/state") Object mafiaState(@RequestHeader("Authorization")String a){return mafia.state(player(a));}
    @PostMapping("/mafia/join") Object mafiaJoin(@RequestHeader("Authorization")String a){return queue.run(()->mafia.join(player(a)));}
    @PostMapping("/mafia/ready") Object mafiaReady(@RequestHeader("Authorization")String a){return queue.run(()->mafia.ready(player(a)));}
    @PostMapping("/mafia/act") Object mafiaAct(@RequestHeader("Authorization")String a,@RequestBody MafiaAction r){return queue.run(()->mafia.act(player(a),r.target));}
    @PostMapping("/mafia/chat") Object mafiaChat(@RequestHeader("Authorization")String a,@RequestBody Chat r){return queue.run(()->mafia.chat(player(a),r.text));}
    @PostMapping("/mafia/leave") Object mafiaLeave(@RequestHeader("Authorization")String a){return queue.run(()->mafia.leave(player(a)));}
    @PostMapping("/mafia/cancel") Object mafiaCancel(@RequestHeader("Authorization")String a){return queue.run(()->mafia.cancel(player(a)));}
    @GetMapping("/admin/players") Object adminPlayers(@RequestHeader("X-Admin-Code")String code){return Map.of("players",service.adminPlayers(code));}
    @PostMapping("/admin/grant") Object grant(@RequestHeader("X-Admin-Code")String code,@RequestBody AdminAction r){return queue.run(()->Map.of("players",service.grantCredits(code,r.playerId,r.amount)));}
    @PostMapping("/admin/kick") Object kick(@RequestHeader("X-Admin-Code")String code,@RequestBody AdminAction r){return queue.run(()->{service.adminPlayers(code);social.removePlayer(r.playerId);mafia.removePlayer(r.playerId);return Map.of("players",service.kick(code,r.playerId));});}
    @GetMapping("/admin/quiz") Object quizAdmin(@RequestHeader("X-Admin-Code")String code){service.adminPlayers(code);return quiz.adminStatus();}
    @PostMapping("/admin/quiz/toggle") Object quizToggle(@RequestHeader("X-Admin-Code")String code,@RequestBody QuizToggle r){service.adminPlayers(code);return queue.run(()->quiz.setGenerationEnabled(r.enabled));}
    record Join(String code,String nickname){} record Bet(long bet){} record RaceBet(long bet,int snail,int snailCount){} record HangmanStart(String opponent,long stake){} record Guess(String letter){} record Leave(String game){} record QuizAnswer(String questionId,int choice){} record QuizToggle(boolean enabled){} record AdminAction(String playerId,long amount){} record Chat(String text){} record YachtRoll(java.util.List<Boolean> held){} record YachtScore(String category,java.util.List<Integer> dice){} record MafiaAction(String target){}
    @ExceptionHandler({IllegalArgumentException.class,SecurityException.class}) ResponseEntity<?> error(RuntimeException e){return ResponseEntity.badRequest().body(Map.of("error",e.getMessage()));}
    @ExceptionHandler(Exception.class) ResponseEntity<?> serverError(Exception e){e.printStackTrace();return ResponseEntity.status(500).body(Map.of("error","서버 처리 중 오류가 발생했습니다: "+e.getClass().getSimpleName()));}
}
