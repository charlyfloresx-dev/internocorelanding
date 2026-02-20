using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
namespace Interno.Gym
{
    public class ScheduledLesson
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public int LessonId { get; set; }

        public Lesson? Lesson { get; set; }
        public int TutorId { get; set; }
        public Tutor? Tutor { get; set; }
        public string? Location { get; set; }
        public string? Description { get; set; }
        public DateTime Start { get; set; }
        public DateTime End { get; set; }

        public ICollection<Partner>? Partners { get; set; }
    }
}