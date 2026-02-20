using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;



namespace Interno.Quality.Models
{
    public class Defect
    {
        [Key]
        public int Id { get; set; }   
        [Required]
        public string Code { get; set; }
        [Required]
        public string Description { get; set; }
        [Required]
        public DefectType Type { get; set; }
        [Required]
        public DefectSource Source { get; set; }
        public Interno.Domain.Enum.StatusType Status { get; set; }

        public ICollection<Defect> SecondLvl { get; set; }
    }

    public enum DefectType
    {
        Funcional,
        Cosmetic,
        Dimensional
    }
    public class DefectSource
    {
        [Key]
        public int Id { get; set; }        
        [Required]
        public string Code { get; set; }
        public string Name { get; set; }
        public string Description { get; set; }
        public Interno.Domain.Enum.StatusType Status { get; set; }
    }
}