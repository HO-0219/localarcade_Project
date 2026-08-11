package com.localarcade.game;

import com.localarcade.player.Player;
import com.localarcade.player.PlayerRepository;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.transaction.annotation.Transactional;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class GameService {
    private final PlayerRepository repo; private final SecureRandom random=new SecureRandom();
    private final Map<String,String> sessions=new ConcurrentHashMap<>();
    private final Map<String,RaceEntry> racers=new LinkedHashMap<>(); private RaceResult lastRace; private static final int RACE_SNAIL_COUNT=5; private Hangman hangman; private String joinCode,adminCode;
    public GameService(PlayerRepository repo){this.repo=repo;}
    @PostConstruct void ready(){repo.deleteAll();joinCode="%06d".formatted(random.nextInt(100000,1000000));adminCode=UUID.randomUUID().toString().substring(0,8).toUpperCase();System.out.println("\n========================================\n  LOCAL ARCADE 참여 코드: "+joinCode+"\n  관리자 페이지: http://localhost:5173/admin\n  관리자 코드: "+adminCode+"\n  백엔드 포트: 8081 / 게임 화면 포트: 5173\n========================================\n");}
    @Scheduled(fixedDelay=30000)
    @Transactional public synchronized void cleanupInactivePlayers(){List<Player>stale=repo.findByLastSeenBefore(Instant.now().minusSeconds(30));for(Player p:stale){sessions.entrySet().removeIf(e->e.getValue().equals(p.getId()));racers.remove(p.getId());if(hangman!=null&&hangman.players.contains(p.getId()))hangman=null;}repo.deleteAll(stale);}
    @Transactional public synchronized String join(String code,String nickname){
        String chosenNickname=nickname==null?"":nickname.trim(); if(!joinCode.equals(code))throw new IllegalArgumentException("참여 코드가 올바르지 않습니다.");
        if(chosenNickname.length()<2||chosenNickname.length()>12)throw new IllegalArgumentException("닉네임은 2~12자로 입력하세요.");
        if(activePlayers().stream().anyMatch(p->p.getNickname().equalsIgnoreCase(chosenNickname)))throw new IllegalArgumentException("현재 접속 중인 닉네임입니다.");
        if(activePlayers().size()>=6)throw new IllegalArgumentException("최대 6명까지 참여할 수 있습니다.");
        Player p=repo.findFirstByNicknameIgnoreCaseOrderByLastSeenDesc(chosenNickname).orElseGet(()->new Player(chosenNickname));p.resetForNewSession();p=repo.save(p);String token=UUID.randomUUID().toString();sessions.put(token,p.getId());return token;
    }
    @Transactional public Player auth(String token){String id=sessions.get(token);if(id==null)throw new SecurityException("다시 참여해 주세요.");Player p=repo.findById(id).orElseThrow();p.touch();return p;}
    public List<Player> activePlayers(){Instant cutoff=Instant.now().minus(Duration.ofSeconds(15));Set<String>sessionPlayerIds=new HashSet<>(sessions.values());return repo.findAll().stream().filter(p->sessionPlayerIds.contains(p.getId())&&p.getLastSeen().isAfter(cutoff)).toList();}
    public synchronized Map<String,Object> state(Player me){
        var ps=activePlayers().stream().map(p->Map.of("id",p.getId(),"nickname",p.getNickname(),"credits",p.getCredits())).toList();
        var race=Map.of("entrants",racers.keySet(),"entries",racers.entrySet().stream().map(e->Map.of("playerId",e.getKey(),"nickname",repo.findById(e.getKey()).map(Player::getNickname).orElse("퇴장"),"snail",e.getValue().snail,"bet",e.getValue().bet)).toList(),"snailCount",RACE_SNAIL_COUNT,"lastResult",lastRace==null?Map.of():lastRace);
        return Map.of("me",view(me),"players",ps,"race",race,"hangman",hangmanView());
    }
    private Map<String,Object> view(Player p){return Map.of("id",p.getId(),"nickname",p.getNickname(),"credits",p.getCredits());}
    @Transactional public synchronized Map<String,Object> race(Player p,String action,long bet,int snail,int snailCount){if("join".equals(action)){allowed(bet,100,500,1000,2500,5000);if(snail<1||snail>RACE_SNAIL_COUNT)throw new IllegalArgumentException("1~5번 달팽이 중에서 선택하세요.");if(racers.containsKey(p.getId()))throw new IllegalArgumentException("이미 참가했습니다.");p.debit(bet);racers.put(p.getId(),new RaceEntry(bet,snail));repo.save(p);}else{if(racers.isEmpty())throw new IllegalArgumentException("참가자가 필요합니다.");List<Integer> order=new ArrayList<>();for(int i=1;i<=RACE_SNAIL_COUNT;i++)order.add(i);Collections.shuffle(order,random);int winnerSnail=order.getFirst();double multiplier=4.5;List<String>winners=new ArrayList<>();for(var entry:racers.entrySet()){if(entry.getValue().snail==winnerSnail){Player winner=repo.findById(entry.getKey()).orElseThrow();winner.credit(Math.round(entry.getValue().bet*multiplier));repo.save(winner);winners.add(winner.getNickname());}}lastRace=new RaceResult(System.currentTimeMillis(),winnerSnail,order,winners,multiplier);racers.clear();}return state(p);}
    @Transactional public synchronized Map<String,Object> startHangman(Player p,String opponentId,long stake){allowed(stake,50,100,250);if(hangman!=null&&!hangman.done)throw new IllegalArgumentException("행맨 대결이 진행 중입니다.");Player o=repo.findById(opponentId).orElseThrow();if(o.getId().equals(p.getId())||!activePlayers().contains(o))throw new IllegalArgumentException("접속 중인 상대를 선택하세요.");p.debit(stake);o.debit(stake);repo.saveAll(List.of(p,o));hangman=new Hangman(List.of(p.getId(),o.getId()),stake,nextWord());return state(p);}
    @Transactional public synchronized Map<String,Object> guess(Player p,String value){if(hangman==null||hangman.done||!hangman.players.contains(p.getId()))throw new IllegalArgumentException("참여 중인 대결이 없습니다.");String letter=value==null?"":value.toUpperCase();if(!letter.matches("[A-Z]"))throw new IllegalArgumentException("영문 한 글자를 입력하세요.");if(!hangman.guessed.add(letter))throw new IllegalArgumentException("이미 선택한 글자입니다.");if(hangman.word.contains(letter)){String opponentId=hangman.players.stream().filter(id->!id.equals(p.getId())).findFirst().orElseThrow();hangman.damage.put(opponentId,hangman.damage.get(opponentId)+1);hangman.message=p.getNickname()+"의 공격 성공!";if(hangman.damage.get(opponentId)>=7){hangman.done=true;hangman.message=p.getNickname()+" 승리!";p.credit(hangman.stake*2);repo.save(p);}else if(hangman.word.chars().allMatch(ch->hangman.guessed.contains(String.valueOf((char)ch)))){hangman.round++;hangman.word=nextWord();hangman.guessed.clear();hangman.message="새 단어 등장! ROUND "+hangman.round;}}else hangman.message=p.getNickname()+"의 공격 실패";return state(p);}
    private String nextWord(){String[]words={"ARCADE","ROCKET","GALAXY","JACKPOT","RACING","PIXEL","PLAYER","MYSTERY","CASTLE","DRAGON","KNIGHT","CROWN"};return words[random.nextInt(words.length)];}
    @Transactional public synchronized Map<String,Object> leave(Player p,String game){
        if("race".equals(game)){racers.remove(p.getId());lastRace=null;}
        if("hangman".equals(game)&&hangman!=null&&hangman.players.contains(p.getId())){if(!hangman.done){String winnerId=hangman.players.stream().filter(id->!id.equals(p.getId())).findFirst().orElse(null);if(winnerId!=null){Player winner=repo.findById(winnerId).orElseThrow();winner.credit(hangman.stake*2);repo.save(winner);}}hangman=null;}
        return state(p);
    }
    private void allowed(long value,long... choices){if(Arrays.stream(choices).noneMatch(x->x==value))throw new IllegalArgumentException("선택할 수 없는 점수입니다.");}
    public synchronized List<Map<String,Object>> adminPlayers(String code){admin(code);return activePlayers().stream().map(this::view).toList();}
    @Transactional public synchronized List<Map<String,Object>> grantCredits(String code,String playerId,long amount){admin(code);if(!List.of(-10000L,-5000L,-1000L,1000L,5000L,10000L).contains(amount))throw new IllegalArgumentException("선택할 수 없는 크레딧 조정값입니다.");Player p=repo.findById(playerId).orElseThrow(()->new IllegalArgumentException("플레이어를 찾을 수 없습니다."));p.adjustCredits(amount);repo.save(p);return adminPlayers(code);}
    @Transactional public synchronized List<Map<String,Object>> kick(String code,String playerId){admin(code);sessions.entrySet().removeIf(e->e.getValue().equals(playerId));racers.remove(playerId);if(hangman!=null&&hangman.players.contains(playerId))hangman=null;repo.deleteById(playerId);return adminPlayers(code);}
    private void admin(String code){if(code==null||!adminCode.equalsIgnoreCase(code))throw new SecurityException("관리자 코드가 올바르지 않습니다.");}
    private Object hangmanView(){if(hangman==null)return Map.of();String masked=hangman.word.chars().mapToObj(c->hangman.done||hangman.guessed.contains(String.valueOf((char)c))?String.valueOf((char)c):"_").reduce((a,b)->a+" "+b).orElse("");return Map.of("players",hangman.players,"names",hangman.players.stream().map(id->repo.findById(id).map(Player::getNickname).orElse("퇴장")).toList(),"damage",hangman.players.stream().map(id->hangman.damage.getOrDefault(id,0)).toList(),"round",hangman.round,"word",masked,"guessed",hangman.guessed,"done",hangman.done,"message",hangman.message);}
    record RaceEntry(long bet,int snail){} record RaceResult(long raceId,int winnerSnail,List<Integer> order,List<String> winners,double multiplier){}
    static class Hangman{List<String>players;long stake;String word;Set<String>guessed=new LinkedHashSet<>();Map<String,Integer>damage=new LinkedHashMap<>();int round=1;boolean done;String message="상대 행맨을 먼저 완성하세요!";Hangman(List<String>p,long s,String w){players=p;stake=s;word=w;p.forEach(id->damage.put(id,0));}}
}
