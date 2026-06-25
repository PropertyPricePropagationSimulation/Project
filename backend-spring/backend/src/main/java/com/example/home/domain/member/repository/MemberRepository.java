package com.example.home.domain.member.repository;

import com.example.home.domain.member.entity.Member;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface MemberRepository {

    Member findById(@Param("id") Long id);

    Member findByEmail(@Param("email") String email);

    boolean existsByEmail(@Param("email") String email);

    void save(Member member);

    void update(Member member);

    void updatePassword(@Param("id") Long id, @Param("password") String password);
    
    void deleteById(@Param("id") Long id);
}
