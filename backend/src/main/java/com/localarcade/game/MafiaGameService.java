package com.localarcade.game;

import com.localarcade.player.Player;
import com.localarcade.player.PlayerRepository;
import org.springframework.stereotype.Service;
import java.time.Instant;
import java.util.*;

@Service
public class MafiaGameService {
    private static final int PHASE_SECONDS=60;
    private final PlayerRepository repo;
    private final LinkedHashSet<String> lobby=new LinkedHashSet<>(),ready=new LinkedHashSet<>();
    private final Deque<MafiaMessage> chat=new ArrayDeque<>();
    private final Random random=new Random();
    private MafiaGame game; private long messageSequence;
    MafiaGameService(PlayerRepository repo){this.repo=repo;}

    public synchronized Map<String,Object> state(Player me){advance();return view(me);}
    public synchronized Map<String,Object> join(Player p){if(game!=null&&!game.finished)throw new IllegalArgumentException("이미 마피아 게임이 진행 중입니다.");if(game!=null&&game.finished){game=null;chat.clear();}if(lobby.size()>=6)throw new IllegalArgumentException("참가 인원이 가득 찼습니다.");lobby.add(p.getId());ready.remove(p.getId());return view(p);}
    public synchronized Map<String,Object> ready(Player p){if(!lobby.contains(p.getId()))throw new IllegalArgumentException("먼저 게임에 참여하세요.");if(ready.contains(p.getId()))ready.remove(p.getId());else ready.add(p.getId());if(lobby.size()>=4&&ready.containsAll(lobby))start();return view(p);}
    public synchronized Map<String,Object> leave(Player p){lobby.remove(p.getId());ready.remove(p.getId());if(game!=null&&!game.finished&&game.alive.remove(p.getId())){game.message=p.getNickname()+"님이 게임에서 나갔습니다.";checkWinner();}return view(p);}
    public synchronized Map<String,Object> cancel(Player p){if(game==null||game.finished||!game.players.contains(p.getId()))throw new IllegalArgumentException("진행 중인 마피아 참가자만 종료할 수 있습니다.");finish(p.getNickname()+"님이 마피아 게임을 종료했습니다.");return view(p);}
    public synchronized Map<String,Object> act(Player p,String target){advance();requireAlive(p);if(target==null||!game.alive.contains(target))throw new IllegalArgumentException("생존한 플레이어를 선택하세요.");if(game.phase.equals("DAY")){if(target.equals(p.getId()))throw new IllegalArgumentException("자기 자신에게 투표할 수 없습니다.");game.votes.put(p.getId(),target);game.message="낮 투표가 진행 중입니다.";}else{String role=game.roles.get(p.getId());if(role.equals("MAFIA")){if(game.roles.get(target).equals("MAFIA"))throw new IllegalArgumentException("마피아는 동료를 지목할 수 없습니다.");game.mafiaVotes.put(p.getId(),target);}else if(role.equals("DOCTOR"))game.doctorTarget=target;else throw new IllegalArgumentException("시민은 밤에 행동할 수 없습니다.");game.message="밤의 선택이 진행 중입니다.";}advance();return view(p);}
    public synchronized Map<String,Object> chat(Player p,String text){advance();requireAlive(p);String clean=text==null?"":text.strip();if(clean.isBlank()||clean.length()>200)throw new IllegalArgumentException("채팅은 1~200자로 입력하세요.");String scope=game.phase.equals("NIGHT")?"MAFIA":"DAY";if(scope.equals("MAFIA")&&!game.roles.get(p.getId()).equals("MAFIA"))throw new IllegalArgumentException("밤에는 마피아만 대화할 수 있습니다.");chat.addLast(new MafiaMessage(++messageSequence,p.getNickname(),clean,scope,game.round,Instant.now().toString()));while(chat.size()>100)chat.removeFirst();return view(p);}
    public synchronized void removePlayer(String id){lobby.remove(id);ready.remove(id);if(game!=null&&!game.finished&&game.alive.remove(id)){game.message="플레이어 퇴장으로 인원이 변경되었습니다.";checkWinner();}}

    private void start(){List<String>players=new ArrayList<>(lobby);Collections.shuffle(players,random);game=new MafiaGame(players);int mafiaCount=players.size()>=6?2:1;for(int i=0;i<players.size();i++)game.roles.put(players.get(i),i<mafiaCount?"MAFIA":i==mafiaCount?"DOCTOR":"CITIZEN");game.alive.addAll(players);lobby.clear();ready.clear();chat.clear();game.message="밤이 되었습니다. 역할을 확인하고 행동하세요.";}
    private void requireAlive(Player p){if(game==null||game.finished)throw new IllegalArgumentException("진행 중인 마피아 게임이 없습니다.");if(!game.alive.contains(p.getId()))throw new IllegalArgumentException("탈락한 플레이어는 행동할 수 없습니다.");}
    private void advance(){if(game==null||game.finished)return;boolean expired=!Instant.now().isBefore(game.phaseEndsAt);if(game.phase.equals("NIGHT")){long mafias=game.alive.stream().filter(id->game.roles.get(id).equals("MAFIA")).count();boolean mafiaDone=game.mafiaVotes.size()>=mafias;Optional<String>doctor=game.alive.stream().filter(id->game.roles.get(id).equals("DOCTOR")).findFirst();boolean doctorDone=doctor.isEmpty()||game.doctorTarget!=null;if(expired||(mafiaDone&&doctorDone))resolveNight();}else if(expired||game.votes.size()>=game.alive.size())resolveDay();}
    private void resolveNight(){String target=plurality(game.mafiaVotes.values());if(target!=null&&!target.equals(game.doctorTarget)){game.alive.remove(target);game.message=name(target)+"님이 밤사이 사라졌습니다.";}else if(target!=null)game.message="의사가 누군가를 살렸습니다!";else game.message="평화로운 밤이 지나갔습니다.";game.mafiaVotes.clear();game.doctorTarget=null;if(checkWinner())return;game.phase="DAY";game.phaseEndsAt=Instant.now().plusSeconds(PHASE_SECONDS);}
    private void resolveDay(){String target=uniquePlurality(game.votes.values());if(target!=null){game.alive.remove(target);game.message=name(target)+"님이 투표로 탈락했습니다.";}else game.message="투표가 동률이라 아무도 탈락하지 않았습니다.";game.votes.clear();if(checkWinner())return;game.phase="NIGHT";game.round++;game.phaseEndsAt=Instant.now().plusSeconds(PHASE_SECONDS);}
    private boolean checkWinner(){if(game==null)return false;long mafia=game.alive.stream().filter(id->game.roles.get(id).equals("MAFIA")).count(),others=game.alive.size()-mafia;if(mafia==0){finish("시민 팀 승리! 모든 마피아를 찾아냈습니다.");return true;}if(mafia>=others){finish("마피아 팀 승리! 마을을 장악했습니다.");return true;}return false;}
    private void finish(String message){game.finished=true;game.phase="FINISHED";game.message=message;game.phaseEndsAt=Instant.now();}
    private String plurality(Collection<String>votes){return votes.stream().collect(java.util.stream.Collectors.groupingBy(x->x,LinkedHashMap::new,java.util.stream.Collectors.counting())).entrySet().stream().max(Map.Entry.comparingByValue()).map(Map.Entry::getKey).orElse(null);}
    private String uniquePlurality(Collection<String>votes){Map<String,Long>counts=votes.stream().collect(java.util.stream.Collectors.groupingBy(x->x,LinkedHashMap::new,java.util.stream.Collectors.counting()));long max=counts.values().stream().mapToLong(x->x).max().orElse(0);return counts.values().stream().filter(x->x==max).count()==1?counts.entrySet().stream().filter(e->e.getValue()==max).map(Map.Entry::getKey).findFirst().orElse(null):null;}
    private String name(String id){return repo.findById(id).map(Player::getNickname).orElse("플레이어");}
    private Map<String,Object> view(Player me){
        Map<String,Object>v=new LinkedHashMap<>();
        v.put("lobby",lobby.stream().map(id->Map.of("playerId",id,"nickname",name(id),"ready",ready.contains(id))).toList());
        v.put("active",game!=null&&!game.finished);v.put("done",game!=null&&game.finished);if(game==null)return v;
        String myRole=game.roles.getOrDefault(me.getId(),"SPECTATOR");boolean mafia=myRole.equals("MAFIA");
        v.put("players",game.players.stream().map(id->Map.of("playerId",id,"nickname",name(id),"alive",game.alive.contains(id),"role",game.finished||id.equals(me.getId())||mafia&&game.roles.get(id).equals("MAFIA")?game.roles.get(id):"HIDDEN")).toList());
        v.put("phase",game.phase);v.put("round",game.round);v.put("remainingSeconds",Math.max(0,game.phaseEndsAt.getEpochSecond()-Instant.now().getEpochSecond()));v.put("message",game.message);v.put("myRole",myRole);v.put("myVote",game.votes.get(me.getId()));
        v.put("myTarget",myRole.equals("MAFIA")?game.mafiaVotes.get(me.getId()):myRole.equals("DOCTOR")?game.doctorTarget:null);
        v.put("acted",game.phase.equals("DAY")?game.votes.containsKey(me.getId()):myRole.equals("MAFIA")?game.mafiaVotes.containsKey(me.getId()):myRole.equals("DOCTOR")&&game.doctorTarget!=null);
        v.put("chat",chat.stream().filter(m->m.scope.equals("DAY")||mafia).toList());return v;
    }

    record MafiaMessage(long id,String nickname,String text,String scope,int round,String sentAt){}
    static class MafiaGame{List<String>players;Set<String>alive=new LinkedHashSet<>();Map<String,String>roles=new LinkedHashMap<>(),votes=new LinkedHashMap<>(),mafiaVotes=new LinkedHashMap<>();String doctorTarget,phase="NIGHT",message;int round=1;boolean finished;Instant phaseEndsAt=Instant.now().plusSeconds(PHASE_SECONDS);MafiaGame(List<String>players){this.players=players;}}
}
