using System.ComponentModel.DataAnnotations;
namespace Interno.Gym
{
    public class Lesson
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public string Name { get; set; }
        [Required]
        public string Room { get; set; }
        public string Description { get; set; }
    }
}