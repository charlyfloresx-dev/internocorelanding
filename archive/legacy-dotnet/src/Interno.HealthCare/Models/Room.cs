using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
namespace Interno.HealthCare.Models
{
    public class Room
    {
        [KeyAttribute]
        public int Id { get; set; }

        public Block Block { get; set; }

        public ICollection<Bed> Beds { get; set; } = new List<Bed>();
    }
}