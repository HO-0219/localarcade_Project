package com.localarcade.player;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "players")
public class Player {
    @Id private String id;
    @Column(nullable=false, length=12) private String nickname;
    @Column(nullable=false) private long credits;
    @Column(nullable=false) private Instant lastSeen;
    protected Player() {}
    public Player(String nickname) { this.id=UUID.randomUUID().toString(); this.nickname=nickname; this.credits=10000; touch(); }
    public String getId(){return id;} public String getNickname(){return nickname;} public long getCredits(){return credits;} public Instant getLastSeen(){return lastSeen;}
    public void touch(){lastSeen=Instant.now();}
    public void resetForNewSession(){credits=10000;touch();}
    public void debit(long amount){if(amount<10||amount>5000)throw new IllegalArgumentException("점수는 10~5,000만 사용할 수 있습니다.");if(credits<amount)throw new IllegalArgumentException("크레딧이 부족합니다.");credits-=amount;}
    public void credit(long amount){credits+=amount;}
    public void adjustCredits(long amount){if(credits+amount<0)throw new IllegalArgumentException("보유 크레딧보다 많이 차감할 수 없습니다.");credits+=amount;}
}
