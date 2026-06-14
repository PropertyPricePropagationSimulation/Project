package com.example.home.domain.qna.repository;

import com.example.home.domain.qna.entity.Qna;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface QnaRepository {

    Qna findById(@Param("id") Long id);

    List<Qna> findAll(@Param("offset") int offset, @Param("size") int size);

    long count();

    void save(Qna qna);

    void update(Qna qna);

    void updateAnswered(@Param("id") Long id, @Param("answered") boolean answered);

    void deleteById(@Param("id") Long id);
}
