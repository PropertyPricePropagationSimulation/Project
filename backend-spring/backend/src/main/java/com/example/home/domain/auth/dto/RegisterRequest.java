package com.example.home.domain.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Past;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

public record RegisterRequest(
        @Email @NotBlank String email,
        @NotBlank @Size(min = 8, max = 20) String password,
        @NotBlank @Size(min = 2, max = 20) String nickname,
        @NotNull @Past LocalDate birthDate
) {
}
