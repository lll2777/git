insert into storage.buckets (id, name, public)
values ('datasets', 'datasets', false)
on conflict (id) do nothing;

drop policy if exists "Authenticated users can upload their dataset files"
on storage.objects;

drop policy if exists "Authenticated users can read their dataset files"
on storage.objects;

drop policy if exists "Authenticated users can update their dataset files"
on storage.objects;

drop policy if exists "Authenticated users can delete their dataset files"
on storage.objects;

create policy "Authenticated users can upload their dataset files"
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'datasets'
  and (storage.foldername(name))[2] = auth.uid()::text
);

create policy "Authenticated users can read their dataset files"
on storage.objects
for select
to authenticated
using (
  bucket_id = 'datasets'
  and (storage.foldername(name))[2] = auth.uid()::text
);

create policy "Authenticated users can update their dataset files"
on storage.objects
for update
to authenticated
using (
  bucket_id = 'datasets'
  and (storage.foldername(name))[2] = auth.uid()::text
)
with check (
  bucket_id = 'datasets'
  and (storage.foldername(name))[2] = auth.uid()::text
);

create policy "Authenticated users can delete their dataset files"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'datasets'
  and (storage.foldername(name))[2] = auth.uid()::text
);
