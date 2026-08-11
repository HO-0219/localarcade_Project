package com.localarcade.game;

import com.localarcade.player.PlayerRepository;
import org.junit.jupiter.api.Test;
import java.lang.reflect.Method;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;

class YachtScoringTest {
    @Test void threeFivesAndTwoThreesIsFullHouse() throws Exception {
        SocialGameService service=new SocialGameService(mock(PlayerRepository.class));
        Method calculate=SocialGameService.class.getDeclaredMethod("calculate",String.class,int[].class);
        calculate.setAccessible(true);
        assertEquals(21,calculate.invoke(service,"FULL_HOUSE",new int[]{5,5,5,3,3}));
        assertEquals(50,calculate.invoke(service,"YACHT",new int[]{5,5,5,5,5}));
    }
}
