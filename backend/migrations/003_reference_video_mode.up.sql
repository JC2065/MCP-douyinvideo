alter table storyboards drop constraint if exists storyboards_reference_mode_check;
alter table storyboards add constraint storyboards_reference_mode_check
  check (reference_mode in ('reference-video','content-structure','visual-style','same-topic'));
