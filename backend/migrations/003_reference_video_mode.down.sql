update storyboards set reference_mode='visual-style' where reference_mode='reference-video';
alter table storyboards drop constraint if exists storyboards_reference_mode_check;
alter table storyboards add constraint storyboards_reference_mode_check
  check (reference_mode in ('content-structure','visual-style','same-topic'));
