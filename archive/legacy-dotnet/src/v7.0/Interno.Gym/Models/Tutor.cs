using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
namespace Interno.Gym
{
    public class Tutor 
    {
        public int PersonId { get; set; }
        public Interno.Domain.Catalog.Person Person { get; set; }
        [NotMapped]
        public ICollection<Lesson>? Lessons { get; set; }
    }
}