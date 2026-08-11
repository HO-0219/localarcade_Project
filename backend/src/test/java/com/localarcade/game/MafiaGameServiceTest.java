package com.localarcade.game;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.localarcade.player.Player;
import com.localarcade.player.PlayerRepository;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class MafiaGameServiceTest {
    @Test void dayChatAndVotingRemainSerializable(){
        PlayerRepository repo=mock(PlayerRepository.class);Map<String,Player>byId=new LinkedHashMap<>();
        List<Player>players=List.of(new Player("하나"),new Player("둘"),new Player("셋"),new Player("넷"));
        players.forEach(p->byId.put(p.getId(),p));when(repo.findById(anyString())).thenAnswer(i->Optional.ofNullable(byId.get(i.getArgument(0))));
        MafiaGameService service=new MafiaGameService(repo);players.forEach(service::join);players.forEach(service::ready);
        Map<String,String>roles=new LinkedHashMap<>();for(Player p:players)roles.put(p.getId(),String.valueOf(service.state(p).get("myRole")));
        Player mafia=players.stream().filter(p->roles.get(p.getId()).equals("MAFIA")).findFirst().orElseThrow();
        Player doctor=players.stream().filter(p->roles.get(p.getId()).equals("DOCTOR")).findFirst().orElseThrow();
        Player victim=players.stream().filter(p->roles.get(p.getId()).equals("CITIZEN")).findFirst().orElseThrow();
        service.act(mafia,victim.getId());service.act(doctor,doctor.getId());
        List<Player>alive=players.stream().filter(p->Boolean.TRUE.equals(playerView(service.state(p),p.getId()).get("alive"))).toList();
        for(Player p:alive){Map<String,Object>state=service.chat(p,"낮 토론 메시지");assertDoesNotThrow(()->new ObjectMapper().writeValueAsString(state));}
        for(Player p:alive){String target=p.getId().equals(mafia.getId())?doctor.getId():mafia.getId();Map<String,Object>state=service.act(p,target);assertDoesNotThrow(()->new ObjectMapper().writeValueAsString(state));}
    }
    @SuppressWarnings("unchecked") private Map<String,Object>playerView(Map<String,Object>state,String id){return((List<Map<String,Object>>)state.get("players")).stream().filter(p->p.get("playerId").equals(id)).findFirst().orElseThrow();}
}
