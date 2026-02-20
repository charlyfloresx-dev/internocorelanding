using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Production.Models
{
    public class Goal
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public string ResourceCode { get; set; }
        [NotMapped]
        public Resource Resource { get; set; }
        [Required]
        public TimeSpan Hour { get; set; }
        [Required]
        public int Qty { get; set; }
    }
}