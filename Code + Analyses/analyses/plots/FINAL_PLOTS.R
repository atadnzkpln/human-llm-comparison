# Pac-Man Win Rate Bar Plot
library(ggplot2)
library(dplyr)
library(patchwork)
library(papaja)

# ---- READ DATA ----
df <- read.csv("pacman_bound.csv")
df$participant_id <- as.character(df$participant_id)

# ---- DEFINE GROUPS ----
top_humans_explicit <- c("7", "1", "13")
top_humans_implicit <- c("4", "2", "10")
best_human_explicit <- "7"
best_human_implicit <- "4"
llms <- c("claude", "deepseek", "gemini", "gpt")

# ---- COMPUTE WIN RATES WITH SE ----
compute_rates <- function(data, condition_val, top_humans, best_human) {
  cond_data <- data %>% filter(condition == condition_val)
  
  # Top 50% humans: compute mean and SE across participants
  top50_per_participant <- cond_data %>%
    filter(participant_id %in% top_humans) %>%
    group_by(level, participant_id) %>%
    summarise(win_rate = mean(won), .groups = "drop")
  
  top50 <- top50_per_participant %>%
    group_by(level) %>%
    summarise(
      se = sd(win_rate) / sqrt(n()),
      win_rate = mean(win_rate),
      .groups = "drop"
    ) %>%
    mutate(group = "Top 50% Humans")
  

  best <- cond_data %>%
    filter(participant_id == best_human) %>%
    group_by(level) %>%
    summarise(win_rate = mean(won), .groups = "drop") %>%
    mutate(group = "Best Human", se = NA_real_)
  

  llm_data <- cond_data %>%
    filter(participant_id %in% llms) %>%
    group_by(level, participant_id) %>%
    summarise(win_rate = mean(won), .groups = "drop") %>%
    mutate(
      group = case_when(
        participant_id == "claude" ~ "Claude",
        participant_id == "deepseek" ~ "DeepSeek",
        participant_id == "gemini" ~ "Gemini",
        participant_id == "gpt" ~ "GPT"
      ),
      se = NA_real_
    ) %>%
    select(level, win_rate, group, se)
  
  bind_rows(top50, best, llm_data)
}

explicit_rates <- compute_rates(df, "explicit", top_humans_explicit, best_human_explicit)
implicit_rates <- compute_rates(df, "implicit", top_humans_implicit, best_human_implicit)

# ---- FACTOR LEVELS ----
group_order <- c("Top 50% Humans", "Best Human", "Claude", "DeepSeek", "Gemini", "GPT")
explicit_rates$group <- factor(explicit_rates$group, levels = group_order)
implicit_rates$group <- factor(implicit_rates$group, levels = group_order)
explicit_rates$level <- factor(explicit_rates$level, labels = c("Level 1", "Level 2", "Level 3"))
implicit_rates$level <- factor(implicit_rates$level, labels = c("Level 1", "Level 2", "Level 3"))

# ---- COLORS ----
group_fills <- c(
  "Top 50% Humans" = "#4393C3",
  "Best Human"     = "#2166AC",
  "Claude"         = "#F4A582",
  "DeepSeek"       = "#D6604D",
  "Gemini"         = "#B2182B",
  "GPT"            = "#67001F"
)

# ---- PLOT FUNCTION ----
make_barplot <- function(data, title_text) {
  ggplot(data, aes(x = level, y = win_rate, fill = group)) +
    geom_bar(stat = "identity", position = position_dodge(width = 0.8),
             width = 0.7, color = "black", linewidth = 0.3) +
    geom_errorbar(
      aes(ymin = win_rate - se, ymax = win_rate + se),
      position = position_dodge(width = 0.8),
      width = 0.15, linewidth = 0.4,
      na.rm = TRUE
    ) +
    scale_fill_manual(values = group_fills) +
    scale_y_continuous(limits = c(0, 1.05), breaks = seq(0, 1, 0.2),
                       expand = c(0, 0)) +
    labs(x = "Complexity Level", y = "Win Rate", title = title_text) +
    theme_apa() +
    theme(legend.position = "none")
}

# ---- COMBINE ----
p_explicit <- make_barplot(explicit_rates, "Explicit Condition")
p_implicit <- make_barplot(implicit_rates, "Implicit Condition")

combined <- (p_explicit | p_implicit) +
  plot_layout(guides = "collect") &
  theme(legend.position = "bottom", legend.title = element_blank()) &
  guides(fill = guide_legend(nrow = 1))

# ---- SAVE ----
ggsave("Figure1_pacman_winrate.png", combined, width = 10, height = 5, dpi = 300)
ggsave("Figure1_pacman_winrate.pdf", combined, width = 10, height = 5)


# Pac-Man RT Per Move Bar Plot
# Explicit condition only, L1-L2, excluding DeepSeek
library(ggplot2)
library(dplyr)
library(papaja)

# ---- READ DATA ----
df <- read.csv("pacman_bound.csv")
df$participant_id <- as.character(df$participant_id)

# ---- FILTER: explicit condition, L1-L2, exclude DeepSeek ----
# RT is based on winning runs only (win_avg_think)
cond_data <- df %>%
  filter(condition == "explicit", level %in% c(1, 2))

# ---- DEFINE GROUPS ----
top_humans <- c("7", "1", "13")
best_human <- "7"
llms <- c("claude", "gemini", "gpt")  # no DeepSeek (missing L2 RT)

# ---- COMPUTE RT PER LEVEL ----
# For humans: use first_avg_think (RT per move on first attempt)
# For LLMs: same measure
# Only include sublevels that were won (where RT is meaningful)

compute_rt <- function(data, pids, is_group = FALSE) {
  sub <- data %>%
    filter(participant_id %in% pids, won == 1, !is.na(win_avg_think))
  
  if (is_group) {
    # First average per participant per level, then average across participants
    per_participant <- sub %>%
      group_by(level, participant_id) %>%
      summarise(mean_rt = mean(win_avg_think), .groups = "drop")
    
    per_participant %>%
      group_by(level) %>%
      summarise(
        se = sd(mean_rt) / sqrt(n()),
        rt = mean(mean_rt),
        .groups = "drop"
      )
  } else {
    sub %>%
      group_by(level) %>%
      summarise(
        rt = mean(win_avg_think),
        se = NA_real_,
        .groups = "drop"
      )
  }
}

# Top 50% humans
top50_rt <- compute_rt(cond_data, top_humans, is_group = TRUE) %>%
  mutate(group = "Top 50% Humans")

# Best human
best_rt <- compute_rt(cond_data, best_human, is_group = FALSE) %>%
  mutate(group = "Best Human")

# Individual LLMs
llm_rt_list <- lapply(llms, function(llm) {
  compute_rt(cond_data, llm, is_group = FALSE) %>%
    mutate(group = case_when(
      llm == "claude" ~ "Claude",
      llm == "gemini" ~ "Gemini",
      llm == "gpt" ~ "GPT"
    ))
})
llm_rt <- bind_rows(llm_rt_list)

# Combine
all_rt <- bind_rows(top50_rt, best_rt, llm_rt)

# ---- FACTOR LEVELS ----
group_order <- c("Top 50% Humans", "Best Human", "Claude", "Gemini", "GPT")
all_rt$group <- factor(all_rt$group, levels = group_order)
all_rt$level <- factor(all_rt$level, labels = c("Level 1", "Level 2"))

# ---- COLORS (same scheme, without DeepSeek) ----
group_fills <- c(
  "Top 50% Humans" = "#4393C3",
  "Best Human"     = "#2166AC",
  "Claude"         = "#F4A582",
  "Gemini"         = "#B2182B",
  "GPT"            = "#67001F"
)

# ---- PLOT ----
p <- ggplot(all_rt, aes(x = level, y = rt, fill = group)) +
  geom_bar(stat = "identity", position = position_dodge(width = 0.8),
           width = 0.7, color = "black", linewidth = 0.3) +
  geom_errorbar(
    aes(ymin = rt - se, ymax = rt + se),
    position = position_dodge(width = 0.8),
    width = 0.15, linewidth = 0.4,
    na.rm = TRUE
  ) +
  scale_fill_manual(values = group_fills) +
  scale_y_continuous(expand = c(0, 0)) +
  labs(x = "Complexity Level", y = "Reaction Time per Move (seconds)") +
  theme_apa() +
  theme(legend.position = "bottom", legend.title = element_blank()) +
  guides(fill = guide_legend(nrow = 1))

# ---- SAVE ----
ggsave("Figure2_pacman_rt.png", p, width = 7, height = 5, dpi = 300)


# Pac-Man Number of Moves Bar Plot
# Shows average number of moves on winning sublevels
library(ggplot2)
library(dplyr)
library(patchwork)
library(papaja)

# ---- READ DATA ----
df <- read.csv("pacman_bound.csv")
df$participant_id <- as.character(df$participant_id)

# ---- DEFINE GROUPS ----
top_humans_explicit <- c("7", "1", "13")
top_humans_implicit <- c("4", "2", "10")
best_human_explicit <- "7"
best_human_implicit <- "4"
llms <- c("claude", "deepseek", "gemini", "gpt")

# ---- COMPUTE MOVES PER LEVEL (winning sublevels only) ----
compute_moves <- function(data, condition_val, top_humans, best_human) {
  cond_data <- data %>%
    filter(condition == condition_val, won == 1, !is.na(winning_moves))
  
  # Top 50% humans
  top50_per_p <- cond_data %>%
    filter(participant_id %in% top_humans) %>%
    group_by(level, participant_id) %>%
    summarise(mean_moves = mean(winning_moves), .groups = "drop")
  
  top50 <- top50_per_p %>%
    group_by(level) %>%
    summarise(
      se = sd(mean_moves) / sqrt(n()),
      moves = mean(mean_moves),
      .groups = "drop"
    ) %>%
    mutate(group = "Top 50% Humans")
  
  # Best human
  best <- cond_data %>%
    filter(participant_id == best_human) %>%
    group_by(level) %>%
    summarise(moves = mean(winning_moves), se = NA_real_, .groups = "drop") %>%
    mutate(group = "Best Human")
  
  # Individual LLMs
  llm_list <- lapply(llms, function(llm_id) {
    llm_name <- case_when(
      llm_id == "claude" ~ "Claude",
      llm_id == "deepseek" ~ "DeepSeek",
      llm_id == "gemini" ~ "Gemini",
      llm_id == "gpt" ~ "GPT"
    )
    sub <- cond_data %>% filter(participant_id == llm_id)
    if (nrow(sub) == 0) return(NULL)
    sub %>%
      group_by(level) %>%
      summarise(moves = mean(winning_moves), se = NA_real_, .groups = "drop") %>%
      mutate(group = llm_name)
  })
  llm_data <- bind_rows(llm_list)
  
  bind_rows(top50, best, llm_data)
}

explicit_moves <- compute_moves(df, "explicit", top_humans_explicit, best_human_explicit)
implicit_moves <- compute_moves(df, "implicit", top_humans_implicit, best_human_implicit)

# ---- FACTOR LEVELS ----
group_order <- c("Top 50% Humans", "Best Human", "Claude", "DeepSeek", "Gemini", "GPT")
explicit_moves$group <- factor(explicit_moves$group, levels = group_order)
implicit_moves$group <- factor(implicit_moves$group, levels = group_order)
explicit_moves$level <- factor(explicit_moves$level, labels = paste("Level", sort(unique(explicit_moves$level))))
implicit_moves$level <- factor(implicit_moves$level, labels = paste("Level", sort(unique(implicit_moves$level))))

# ---- COLORS ----
group_fills <- c(
  "Top 50% Humans" = "#4393C3",
  "Best Human"     = "#2166AC",
  "Claude"         = "#F4A582",
  "DeepSeek"       = "#D6604D",
  "Gemini"         = "#B2182B",
  "GPT"            = "#67001F"
)

# ---- PLOT FUNCTION ----
make_barplot <- function(data, title_text) {
  ggplot(data, aes(x = level, y = moves, fill = group)) +
    geom_bar(stat = "identity", position = position_dodge(width = 0.8),
             width = 0.7, color = "black", linewidth = 0.3) +
    geom_errorbar(
      aes(ymin = moves - se, ymax = moves + se),
      position = position_dodge(width = 0.8),
      width = 0.15, linewidth = 0.4,
      na.rm = TRUE
    ) +
    scale_fill_manual(values = group_fills) +
    scale_y_continuous(expand = c(0, 0)) +
    labs(x = "Complexity Level", y = "Number of Moves", title = title_text) +
    theme_apa() +
    theme(legend.position = "none")
}

# ---- COMBINE ----
p_explicit <- make_barplot(explicit_moves, "Explicit Condition")
p_implicit <- make_barplot(implicit_moves, "Implicit Condition")

combined <- (p_explicit | p_implicit) +
  plot_layout(guides = "collect") &
  theme(legend.position = "bottom", legend.title = element_blank()) &
  guides(fill = guide_legend(nrow = 1))

# ---- SAVE ----
ggsave("Figure3_pacman_moves.png", combined, width = 10, height = 5, dpi = 300)


# Language Task Bar Plots
# Verdict accuracy and word extraction accuracy combined
library(ggplot2)
library(dplyr)
library(patchwork)
library(papaja)

# ---- READ DATA ----
df <- read.csv("language_jasp.csv")
df$participant_id <- as.character(df$participant_id)

# ---- DEFINE GROUPS ----
# Top 50% humans for language (ranked by overall verdict accuracy)
top_humans <- c("11", "7", "8", "2", "5", "1")
best_human <- "11"  # highest overall verdict accuracy
llms <- c("claude", "deepseek", "gemini", "gpt")

# ---- RESHAPE AND COMPUTE ----
compute_lang_rates <- function(data, dv_prefix, top_h, best_h) {
  # Get the columns for this DV
  cols <- grep(paste0("^", dv_prefix), names(data), value = TRUE)
  levels <- c("low", "medium", "high", "maximum")
  
  results <- list()
  
  for (i in seq_along(levels)) {
    col <- paste0(dv_prefix, "_", levels[i])
    
    # Top 50% humans
    top_vals <- data %>%
      filter(participant_id %in% top_h) %>%
      pull(!!sym(col))
    
    results[[length(results) + 1]] <- data.frame(
      level = levels[i],
      accuracy = mean(top_vals, na.rm = TRUE),
      se = sd(top_vals, na.rm = TRUE) / sqrt(sum(!is.na(top_vals))),
      group = "Top 50% Humans"
    )
    
    # Best human
    best_val <- data %>%
      filter(participant_id == best_h) %>%
      pull(!!sym(col))
    
    results[[length(results) + 1]] <- data.frame(
      level = levels[i],
      accuracy = best_val,
      se = NA_real_,
      group = "Best Human"
    )
    
    # Individual LLMs
    for (llm_id in llms) {
      llm_name <- case_when(
        llm_id == "claude" ~ "Claude",
        llm_id == "deepseek" ~ "DeepSeek",
        llm_id == "gemini" ~ "Gemini",
        llm_id == "gpt" ~ "GPT"
      )
      llm_val <- data %>%
        filter(participant_id == llm_id) %>%
        pull(!!sym(col))
      
      if (length(llm_val) > 0 && !is.na(llm_val)) {
        results[[length(results) + 1]] <- data.frame(
          level = levels[i],
          accuracy = llm_val,
          se = NA_real_,
          group = llm_name
        )
      }
    }
  }
  
  bind_rows(results)
}

verdict_data <- compute_lang_rates(df, "verdict_accuracy", top_humans, best_human)
words_data <- compute_lang_rates(df, "words_accuracy", top_humans, best_human)

# ---- FACTOR LEVELS ----
group_order <- c("Top 50% Humans", "Best Human", "Claude", "DeepSeek", "Gemini", "GPT")
level_labels <- c("Low", "Medium", "High", "Maximum")

verdict_data$group <- factor(verdict_data$group, levels = group_order)
verdict_data$level <- factor(verdict_data$level, levels = c("low", "medium", "high", "maximum"),
                             labels = level_labels)

words_data$group <- factor(words_data$group, levels = group_order)
words_data$level <- factor(words_data$level, levels = c("low", "medium", "high", "maximum"),
                           labels = level_labels)

# ---- COLORS ----
group_fills <- c(
  "Top 50% Humans" = "#4393C3",
  "Best Human"     = "#2166AC",
  "Claude"         = "#F4A582",
  "DeepSeek"       = "#D6604D",
  "Gemini"         = "#B2182B",
  "GPT"            = "#67001F"
)

# ---- PLOT FUNCTION ----
make_barplot <- function(data, title_text, ylab_text) {
  ggplot(data, aes(x = level, y = accuracy, fill = group)) +
    geom_bar(stat = "identity", position = position_dodge(width = 0.8),
             width = 0.7, color = "black", linewidth = 0.3) +
    geom_errorbar(
      aes(ymin = accuracy - se, ymax = accuracy + se),
      position = position_dodge(width = 0.8),
      width = 0.15, linewidth = 0.4,
      na.rm = TRUE
    ) +
    scale_fill_manual(values = group_fills) +
    scale_y_continuous(limits = c(0, 1.05), breaks = seq(0, 1, 0.2),
                       expand = c(0, 0)) +
    labs(x = "Complexity Level", y = ylab_text, title = title_text) +
    theme_apa() +
    theme(legend.position = "none")
}

# ---- COMBINE ----
p_verdict <- make_barplot(verdict_data, "Verdict Accuracy", "Accuracy")
p_words <- make_barplot(words_data, "Word Extraction Accuracy", "Accuracy")

combined <- (p_verdict | p_words) +
  plot_layout(guides = "collect") &
  theme(legend.position = "bottom", legend.title = element_blank()) &
  guides(fill = guide_legend(nrow = 1))

# ---- SAVE ----
ggsave("Figure4_language_accuracy.png", combined, width = 10, height = 5, dpi = 300)


# GLMM Predicted Win Probability Figure
library(ggplot2)
library(papaja)

# ---- GLMM COEFFICIENTS (from JASP output, top 50% humans) ----
intercept <- 2.073
agent_type_coef <- -0.266  # sum coding: human = +1, LLM = -1
sublevel_coef <- -0.302
interaction_coef <- 0.285

# ---- COMPUTE PREDICTED PROBABILITIES ----
sublevels <- 1:18

# Human (coded as +1)
human_logit <- (intercept + agent_type_coef) + (sublevel_coef + interaction_coef) * sublevels
human_prob <- 1 / (1 + exp(-human_logit))

# LLM (coded as -1)
llm_logit <- (intercept - agent_type_coef) + (sublevel_coef - interaction_coef) * sublevels
llm_prob <- 1 / (1 + exp(-llm_logit))

# Combine into data frame
pred_df <- data.frame(
  sublevel = rep(sublevels, 2),
  probability = c(human_prob, llm_prob),
  agent_type = rep(c("Human", "LLM"), each = 18)
)

# ---- SUBLEVEL LABELS ----
sublevel_labels <- paste0(rep(1:3, each = 6), c("A", "B", "C", "D", "E", "F"))

# ---- LEVEL TRANSITION LINES ----
# Level 1 ends at sublevel 6 (1F), Level 2 starts at sublevel 7 (2A)
# Level 2 ends at sublevel 12 (2F), Level 3 starts at sublevel 13 (3A)
transitions <- c(6.5, 12.5)

# ---- PLOT ----
p <- ggplot(pred_df, aes(x = sublevel, y = probability, 
                         shape = agent_type, fill = agent_type)) +
  geom_vline(xintercept = transitions, linetype = "dashed", color = "grey50", linewidth = 0.5) +
  geom_line(aes(group = agent_type), linewidth = 0.6) +
  geom_point(size = 2.5, stroke = 0.6) +
  scale_shape_manual(values = c("Human" = 21, "LLM" = 16)) +
  scale_fill_manual(values = c("Human" = "white", "LLM" = "black")) +
  scale_x_continuous(
    breaks = c(1, 6, 7, 12, 13, 18),
    labels = c("1A", "1F", "2A", "2F", "3A", "3F")
  ) +
  scale_y_continuous(limits = c(0, 1), breaks = seq(0, 1, 0.2)) +
  labs(
    x = "Sublevel",
    y = "Predicted Win Probability"
  ) +
  theme_apa() +
  theme(
    legend.position = c(0.85, 0.5),
    legend.title = element_text(size = 10, face = "bold"),
    legend.text = element_text(size = 9),
    legend.background = element_rect(fill = "white", color = NA)
  ) +
  guides(
    shape = guide_legend(title = "Agent Type"),
    fill = guide_legend(title = "Agent Type")
  )

# ---- SAVE ----
ggsave("Figure_GLMM_trajectory.png", p, width = 7, height = 5, dpi = 300)

