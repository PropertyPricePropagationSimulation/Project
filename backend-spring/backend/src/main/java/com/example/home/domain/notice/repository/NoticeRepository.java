package com.example.home.domain.notice.repository;

import com.example.home.domain.notice.entity.Notice;
import java.util.List;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface NoticeRepository {

    Notice findById(@Param("id") Long id);

    List<Notice> findAll(@Param("offset") int offset, @Param("size") int size);

    long count();

    void save(Notice notice);

    void update(Notice notice);

    void deleteById(@Param("id") Long id);
}
