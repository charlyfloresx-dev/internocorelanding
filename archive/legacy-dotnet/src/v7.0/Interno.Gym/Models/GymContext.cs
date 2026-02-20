using Microsoft.EntityFrameworkCore;

namespace Interno.Gym.Models;

public class GymContext : DbContext
{
    public GymContext(DbContextOptions<GymContext> options) : base(options) { }
    public DbSet<Interno.Gym.Lesson> Lessons { get; set; } = default!;
    public DbSet<Interno.Gym.Tutor> Tutors { get; set; } = default!;
    public DbSet<Interno.Gym.ScheduledLesson> ScheduledLessons { get; set; } = default!;
    public DbSet<Interno.Gym.Partner> Partners { get; set; } = default!;
    public DbSet<Interno.Gym.Subscription> Subscriptions { get; set; } = default!;
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Partner>().Ignore(r => r.Subscriptions).Ignore(r => r.Person);
        modelBuilder.Entity<Tutor>().Ignore(r => r.Lessons).Ignore(r => r.Person);
        modelBuilder.Entity<Partner>().Ignore(r => r.Person);
    }
}